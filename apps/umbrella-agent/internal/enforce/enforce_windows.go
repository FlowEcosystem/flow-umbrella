//go:build windows

package enforce

import (
	"net"
	"os/exec"
	"strings"
)

// ── Domain blocking (DNS sinkhole) ───────────────────────────────────────────

func applyHosts(domains []string, stateFile string) error {
	return applyDNSSinkhole(domains, stateFile)
}

// ── WFP-based IP blocking ────────────────────────────────────────────────────

func applyFirewall(ips []string, stateFile string) error {
	desired := make(map[string]filterSpec)
	for _, ip := range ips {
		if net.ParseIP(ip) == nil {
			continue
		}
		s := filterSpec{ip: ip}
		desired[s.key()] = s
	}

	existing := wfpLoadState(stateFile)

	engine, err := wfpOpenEngine()
	if err != nil {
		return err
	}
	defer wfpCloseEngine(engine)

	if err := wfpBeginTx(engine); err != nil {
		return err
	}
	committed := false
	defer func() {
		if !committed {
			wfpAbortTx(engine)
		}
	}()

	if err := wfpEnsureSublayer(engine); err != nil {
		return err
	}

	for key, id := range existing {
		if _, ok := desired[key]; !ok {
			wfpDeleteFilter(engine, id)
			delete(existing, key)
		}
	}

	for key, spec := range desired {
		if _, ok := existing[key]; !ok {
			id, err := wfpAddFilter(engine, spec)
			if err != nil {
				return err
			}
			existing[key] = id
		}
	}

	if err := wfpCommitTx(engine); err != nil {
		return err
	}
	committed = true

	return wfpSaveState(stateFile, existing)
}

// ── Process enforcement ──────────────────────────────────────────────────────

func applyProcessBlock(names []string) error {
	if len(names) == 0 {
		return nil
	}
	out, err := exec.Command("tasklist", "/FO", "CSV", "/NH").Output()
	if err != nil {
		return err
	}
	blocked := make(map[string]struct{}, len(names))
	for _, n := range names {
		blocked[strings.ToLower(n)] = struct{}{}
	}
	for _, line := range strings.Split(string(out), "\n") {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		fields := strings.SplitN(line, ",", 2)
		if len(fields) == 0 {
			continue
		}
		name := strings.Trim(fields[0], `"`)
		if _, ok := blocked[strings.ToLower(name)]; ok {
			exec.Command("taskkill", "/F", "/IM", name).Run()
		}
	}
	return nil
}
