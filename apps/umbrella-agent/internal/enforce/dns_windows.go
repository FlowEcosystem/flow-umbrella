//go:build windows

package enforce

import (
	"encoding/binary"
	"encoding/json"
	"fmt"
	"net"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"golang.org/x/sys/windows/registry"
)

// dnsSinkhole is a minimal UDP DNS server: NXDOMAIN for blocked domains,
// forward everything else to the upstream resolver.
type dnsSinkhole struct {
	blocked  atomic.Pointer[map[string]struct{}]
	upstream string
	conn     *net.UDPConn
	done     chan struct{}
	wg       sync.WaitGroup
}

var (
	sinkholeMu sync.Mutex
	activeSink *dnsSinkhole
	savedDNS   map[string][]string // interface → original DNS servers (in-memory cache)
)

const (
	nrptBase = `SOFTWARE\Policies\Microsoft\Windows NT\DNSClient\DnsPolicyConfig`
	nrptKey  = `{B4D7E3A2-4C9F-4E2A-8F5C-000000000001}`
)

// applyDNSSinkhole starts/updates/stops the local DNS sinkhole.
// Called with the full current list of blocked domains on every policy cycle.
func applyDNSSinkhole(domains []string, stateFile string) error {
	sinkholeMu.Lock()
	defer sinkholeMu.Unlock()

	if len(domains) == 0 {
		if activeSink != nil {
			activeSink.stop()
			activeSink = nil
			restoreSystemDNS(stateFile)
		}
		return nil
	}

	if activeSink == nil {
		upstream, err := captureAndSetSystemDNS(stateFile)
		if err != nil {
			return fmt.Errorf("set system dns: %w", err)
		}
		s := &dnsSinkhole{upstream: upstream, done: make(chan struct{})}
		if err := s.start(); err != nil {
			restoreSystemDNS(stateFile)
			return fmt.Errorf("start dns sinkhole: %w", err)
		}
		activeSink = s
	}

	// Hot-swap the blocked set without restarting the server.
	m := make(map[string]struct{}, len(domains))
	for _, d := range domains {
		m[strings.ToLower(strings.TrimSuffix(d, "."))] = struct{}{}
	}
	activeSink.blocked.Store(&m)
	refreshInterfaceDNS(stateFile)
	return nil
}

// ── Server ────────────────────────────────────────────────────────────────────

func (s *dnsSinkhole) start() error {
	conn, err := net.ListenPacket("udp", "127.0.0.1:53")
	if err != nil {
		return err
	}
	s.conn = conn.(*net.UDPConn)
	s.wg.Add(1)
	go s.serve()
	return nil
}

func (s *dnsSinkhole) stop() {
	close(s.done)
	s.conn.Close()
	s.wg.Wait()
}

func (s *dnsSinkhole) serve() {
	defer s.wg.Done()
	buf := make([]byte, 512)
	for {
		n, addr, err := s.conn.ReadFromUDP(buf)
		if err != nil {
			select {
			case <-s.done:
				return
			default:
				continue
			}
		}
		pkt := make([]byte, n)
		copy(pkt, buf[:n])
		go s.handle(pkt, addr)
	}
}

func (s *dnsSinkhole) handle(query []byte, addr *net.UDPAddr) {
	if len(query) < 12 {
		return
	}
	name, _, err := dnsReadName(query, 12)
	if err == nil && s.isBlocked(name) {
		s.conn.WriteToUDP(dnsNXDomain(query), addr) //nolint:errcheck
		return
	}
	resp, err := s.forward(query)
	if err != nil {
		// Return SERVFAIL so the client fails fast instead of timing out.
		s.conn.WriteToUDP(dnsSERVFAIL(query), addr) //nolint:errcheck
		return
	}
	s.conn.WriteToUDP(resp, addr) //nolint:errcheck
}

func (s *dnsSinkhole) isBlocked(name string) bool {
	name = strings.ToLower(strings.TrimSuffix(name, "."))
	ptr := s.blocked.Load()
	if ptr == nil {
		return false
	}
	m := *ptr
	if _, ok := m[name]; ok {
		return true
	}
	// Subdomain check: "store.steam.com" is blocked by rule "steam.com".
	for domain := range m {
		if strings.HasSuffix(name, "."+domain) {
			return true
		}
	}
	return false
}

func (s *dnsSinkhole) forward(query []byte) ([]byte, error) {
	conn, err := net.DialTimeout("udp", s.upstream, 3*time.Second)
	if err != nil {
		return nil, err
	}
	defer conn.Close()
	conn.SetDeadline(time.Now().Add(3 * time.Second))
	if _, err := conn.Write(query); err != nil {
		return nil, err
	}
	buf := make([]byte, 4096)
	n, err := conn.Read(buf)
	if err != nil {
		return nil, err
	}
	return buf[:n], nil
}

// ── DNS packet helpers ────────────────────────────────────────────────────────

func dnsReadName(pkt []byte, off int) (string, int, error) {
	var parts []string
	for {
		if off >= len(pkt) {
			return "", 0, fmt.Errorf("dns: truncated")
		}
		l := int(pkt[off])
		if l == 0 {
			return strings.Join(parts, "."), off + 1, nil
		}
		if l&0xC0 == 0xC0 {
			if off+1 >= len(pkt) {
				return "", 0, fmt.Errorf("dns: bad pointer")
			}
			ptr := int(binary.BigEndian.Uint16(pkt[off:]) & 0x3FFF)
			suffix, _, err := dnsReadName(pkt, ptr)
			if err != nil {
				return "", 0, err
			}
			if len(parts) > 0 {
				return strings.Join(parts, ".") + "." + suffix, off + 2, nil
			}
			return suffix, off + 2, nil
		}
		off++
		if off+l > len(pkt) {
			return "", 0, fmt.Errorf("dns: truncated label")
		}
		parts = append(parts, string(pkt[off:off+l]))
		off += l
	}
}

// dnsNXDomain builds an NXDOMAIN response (domain does not exist).
func dnsNXDomain(q []byte) []byte {
	r := make([]byte, len(q))
	copy(r, q)
	r[2] = 0x80 | (q[2] & 0x01) // QR=1, keep RD
	r[3] = 0x83                  // RA=1, RCODE=3 (NXDOMAIN)
	r[6], r[7] = 0, 0
	r[8], r[9] = 0, 0
	r[10], r[11] = 0, 0
	return r
}

// dnsSERVFAIL builds a SERVFAIL response so clients fail fast, not timeout.
func dnsSERVFAIL(q []byte) []byte {
	r := make([]byte, len(q))
	copy(r, q)
	r[2] = 0x80 | (q[2] & 0x01) // QR=1, keep RD
	r[3] = 0x82                  // RA=1, RCODE=2 (SERVFAIL)
	r[6], r[7] = 0, 0
	r[8], r[9] = 0, 0
	r[10], r[11] = 0, 0
	return r
}

// ── DNS state persistence ─────────────────────────────────────────────────────

type dnsPersistedState struct {
	Upstream string              `json:"upstream"`
	DNS      map[string][]string `json:"dns"`
}

func dnsStatePath(stateFile string) string {
	return filepath.Join(filepath.Dir(stateFile), "dns-state.json")
}

func saveDNSStateToDisk(stateFile, upstream string, dns map[string][]string) error {
	s := dnsPersistedState{Upstream: upstream, DNS: dns}
	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(dnsStatePath(stateFile), data, 0o644)
}

func loadDNSStateFromDisk(stateFile string) *dnsPersistedState {
	data, err := os.ReadFile(dnsStatePath(stateFile))
	if err != nil {
		return nil
	}
	var s dnsPersistedState
	if err := json.Unmarshal(data, &s); err != nil {
		return nil
	}
	// Discard state saved with wrong OEM encoding (legacy bug: netsh output
	// was read as UTF-8 on non-English Windows, producing replacement chars).
	for name := range s.DNS {
		if strings.ContainsRune(name, '�') {
			os.Remove(dnsStatePath(stateFile))
			return nil
		}
	}
	return &s
}

func deleteDNSStateFromDisk(stateFile string) {
	os.Remove(dnsStatePath(stateFile))
}

// ── System DNS management ─────────────────────────────────────────────────────

// captureAndSetSystemDNS saves the current DNS configuration to disk,
// sets 127.0.0.1 on all active interfaces, and returns the upstream address.
// If a saved state already exists on disk (crash recovery), the saved upstream
// is reused but DNS is always re-applied — the previous run may have restored
// it or the system may have overwritten it via DHCP renewal.
func captureAndSetSystemDNS(stateFile string) (string, error) {
	var ifaces []string
	var upstream string

	if saved := loadDNSStateFromDisk(stateFile); saved != nil {
		// Crash recovery: reuse the original upstream and saved DNS map so
		// restoreSystemDNS can put things back, but re-apply 127.0.0.1 below.
		savedDNS = saved.DNS
		upstream = saved.Upstream
		for iface := range saved.DNS {
			ifaces = append(ifaces, iface)
		}
	} else {
		var dns map[string][]string
		ifaces, dns = getInterfaceDNS()
		savedDNS = dns

		upstream = "8.8.8.8:53"
		for _, servers := range dns {
			for _, s := range servers {
				if s != "127.0.0.1" {
					upstream = s + ":53"
					goto found
				}
			}
		}
	found:
		// Persist before changing anything — if we crash mid-way, next run recovers.
		if err := saveDNSStateToDisk(stateFile, upstream, dns); err != nil {
			return "", err
		}
	}

	// Always (re-)apply 127.0.0.1, even on crash recovery — the system may
	// have overwritten it while the agent was down.
	for _, iface := range ifaces {
		exec.Command("netsh", "interface", "ipv4", "set", "dnsservers",
			iface, "static", "127.0.0.1", "primary").Run()
	}
	disableBrowserDoH()
	addNRPTCatchAll() //nolint:errcheck
	exec.Command("ipconfig", "/flushdns").Run()
	return upstream, nil
}

// restoreSystemDNS restores the original DNS on all interfaces and removes
// the persisted state file.
func restoreSystemDNS(stateFile string) {
	// Load from disk if in-memory cache is empty (e.g. after agent restart).
	if savedDNS == nil {
		if saved := loadDNSStateFromDisk(stateFile); saved != nil {
			savedDNS = saved.DNS
		}
	}
	if savedDNS == nil {
		return
	}

	removeNRPTCatchAll()
	for iface, servers := range savedDNS {
		if len(servers) == 0 {
			exec.Command("netsh", "interface", "ipv4", "set", "dnsservers",
				iface, "dhcp").Run()
		} else {
			exec.Command("netsh", "interface", "ipv4", "set", "dnsservers",
				iface, "static", servers[0], "primary").Run()
			for _, s := range servers[1:] {
				exec.Command("netsh", "interface", "ipv4", "add", "dnsservers",
					iface, s).Run()
			}
		}
	}
	restoreBrowserDoH()
	exec.Command("ipconfig", "/flushdns").Run()

	savedDNS = nil
	deleteDNSStateFromDisk(stateFile)
}

// getInterfaceDNS returns active (non-loopback) interface names and their
// current DNS servers.
//
// PowerShell's Get-DnsClientServerAddress is used instead of
// `netsh interface ipv4 show dnsservers` because netsh outputs text in the
// system OEM codepage (CP866 on Russian Windows), which corrupts non-ASCII
// interface names when read as UTF-8. PowerShell always outputs Unicode.
func getInterfaceDNS() ([]string, map[string][]string) {
	// Each output line: "<InterfaceAlias>|<ip1>,<ip2>" (empty after | = no servers).
	const script = `[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; ` +
		`Get-DnsClientServerAddress -AddressFamily IPv4 | ` +
		`Where-Object { $_.InterfaceAlias -notlike '*Loopback*' } | ` +
		`ForEach-Object { $_.InterfaceAlias + '|' + ($_.ServerAddresses -join ',') }`

	out, err := exec.Command(
		"powershell", "-NoProfile", "-NonInteractive", "-Command", script,
	).Output()
	if err != nil {
		return nil, nil
	}

	var ifaces []string
	dns := make(map[string][]string)

	for _, line := range strings.Split(string(out), "\n") {
		line = strings.TrimSpace(strings.TrimRight(line, "\r"))
		if line == "" {
			continue
		}
		parts := strings.SplitN(line, "|", 2)
		if len(parts) != 2 {
			continue
		}
		name := parts[0]
		if name == "" {
			continue
		}
		ifaces = append(ifaces, name)
		if parts[1] == "" {
			dns[name] = nil
			continue
		}
		var servers []string
		for _, s := range strings.Split(parts[1], ",") {
			s = strings.TrimSpace(s)
			if ip := net.ParseIP(s); ip != nil && !ip.IsLoopback() {
				servers = append(servers, ip.String())
			}
		}
		dns[name] = servers
	}
	return ifaces, dns
}

// ── NRPT (Name Resolution Policy Table) ──────────────────────────────────────

// addNRPTCatchAll installs a catch-all NRPT rule that routes all DNS queries
// through 127.0.0.1. NRPT takes precedence over per-interface DNS settings,
// so VPN adapters that set their own DNS server are covered automatically.
func addNRPTCatchAll() error {
	k, _, err := registry.CreateKey(registry.LOCAL_MACHINE,
		nrptBase+`\`+nrptKey, registry.SET_VALUE)
	if err != nil {
		return fmt.Errorf("create NRPT rule: %w", err)
	}
	defer k.Close()
	k.SetDWordValue("Version", 2)
	k.SetStringsValue("Name", []string{"."})
	k.SetStringValue("GenericDNSServers", "127.0.0.1")
	return k.SetDWordValue("ConfigOptions", 0x8) // bit 3 = use GenericDNSServers
}

func removeNRPTCatchAll() {
	registry.DeleteKey(registry.LOCAL_MACHINE, nrptBase+`\`+nrptKey) //nolint:errcheck
}

// refreshInterfaceDNS applies 127.0.0.1 to any interfaces that appeared after
// the sinkhole started (e.g. a VPN adapter that connected mid-session).
// New interfaces are added to savedDNS so they are restored on shutdown.
// Must be called with sinkholeMu held.
func refreshInterfaceDNS(stateFile string) {
	if savedDNS == nil {
		return
	}
	ifaces, dns := getInterfaceDNS()
	var added bool
	for _, iface := range ifaces {
		if _, known := savedDNS[iface]; known {
			continue
		}
		savedDNS[iface] = dns[iface]
		exec.Command("netsh", "interface", "ipv4", "set", "dnsservers",
			iface, "static", "127.0.0.1", "primary").Run()
		added = true
	}
	if added {
		upstream := ""
		if activeSink != nil {
			upstream = activeSink.upstream
		}
		saveDNSStateToDisk(stateFile, upstream, savedDNS) //nolint:errcheck
		exec.Command("ipconfig", "/flushdns").Run()
	}
}
