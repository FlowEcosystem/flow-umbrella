package main

import (
	"fmt"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"golang.org/x/term"

	"github.com/flow-ecosystem/umbrella-agent/internal/config"
	"github.com/flow-ecosystem/umbrella-agent/internal/enforce"
	"github.com/flow-ecosystem/umbrella-agent/internal/metrics"
	"github.com/flow-ecosystem/umbrella-agent/internal/state"
)

const autoRefresh = 3 * time.Second

// dashW is the usable content width inside the box (between margins).
// Full line = "  ║  " (5) + dashW (52) + "  ║" (3) = 60 visible chars.
const dashW = 52

func doMonitor(cfgFile string) {
	cfg, err := config.Load(cfgFile)
	if err != nil {
		fatalf("load config: %v", err)
	}

	fd := int(os.Stdin.Fd())

	if !term.IsTerminal(fd) {
		s, _ := state.Load(cfg.StateFile)
		svcSt, _ := serviceStatus()
		renderDashboard(cfg, s, svcSt, false, "")
		return
	}

	oldState, err := term.MakeRaw(fd)
	if err != nil {
		s, _ := state.Load(cfg.StateFile)
		svcSt, _ := serviceStatus()
		renderDashboard(cfg, s, svcSt, false, "")
		return
	}
	defer term.Restore(fd, oldState)
	defer fmt.Print("\033[?25h\033[2J\033[H")

	fmt.Print("\033[?25l")

	keys := make(chan byte, 8)
	go func() {
		buf := make([]byte, 1)
		for {
			if n, _ := os.Stdin.Read(buf); n > 0 {
				select {
				case keys <- buf[0]:
				default:
				}
			}
		}
	}()

	sigs := make(chan os.Signal, 1)
	signal.Notify(sigs, syscall.SIGINT, syscall.SIGTERM)
	defer signal.Stop(sigs)

	tick := time.NewTicker(autoRefresh)
	defer tick.Stop()

	redraw := func() {
		s, _ := state.Load(cfg.StateFile)
		svcSt, _ := serviceStatus()
		renderDashboard(cfg, s, svcSt, true, "[q] quit   [r] refresh   auto-refresh: 3s")
	}
	redraw()

	for {
		select {
		case <-sigs:
			return
		case k := <-keys:
			switch k {
			case 'q', 'Q', 3:
				return
			case 'r', 'R':
				redraw()
				tick.Reset(autoRefresh)
			}
		case <-tick.C:
			redraw()
		}
	}
}

// ── Box drawing helpers ───────────────────────────────────────────────────────

func dashTop() string { return "  ╔" + strings.Repeat("═", dashW+4) + "╗" }
func dashBot() string { return "  ╚" + strings.Repeat("═", dashW+4) + "╝" }

func dashRow(content string) string {
	pad := dashW - visLen(content)
	if pad < 0 {
		pad = 0
	}
	return "  ║  " + content + strings.Repeat(" ", pad) + "  ║"
}

// dashSec renders a section separator: "  ╠══ TITLE ══...══╣"
func dashSec(title, ansiTitle string) string {
	rest := dashW - len(title)
	if rest < 2 {
		rest = 2
	}
	return "  ╠══ " + ansiTitle + " " + strings.Repeat("═", rest) + "╣"
}

// ── renderDashboard ───────────────────────────────────────────────────────────

func renderDashboard(cfg config.Config, s *state.State, svcSt string, ansi bool, hint string) {
	now := time.Now()

	c := func(code, text string) string {
		if !ansi {
			return text
		}
		return "\033[" + code + "m" + text + "\033[0m"
	}

	// key-value row: dim 13-char label + value
	kv := func(key, val string) string {
		return dashRow(c("2", fmt.Sprintf("%-13s", key)) + val)
	}

	sec := func(title string) string {
		return dashSec(title, c("1", title))
	}

	// Collect live metrics (~200ms on Linux due to CPU sampling).
	// Only in interactive mode to avoid blocking non-tty output.
	var snap *metrics.Snapshot
	if ansi {
		if m, err := metrics.Collect(); err == nil {
			snap = &m
		}
	}

	if ansi {
		fmt.Print("\033[2J\033[H")
	}

	// ── Header ──────────────────────────────────────────────────────────────
	fmt.Println(dashTop())
	ts := now.Format("15:04:05")
	hTitle := "UMBRELLA AGENT"
	hPad := dashW - len(hTitle) - len(ts)
	if hPad < 1 {
		hPad = 1
	}
	fmt.Println(dashRow(c("1;36", hTitle) + strings.Repeat(" ", hPad) + c("2", ts)))

	// ── SERVICE ─────────────────────────────────────────────────────────────
	fmt.Println(sec("SERVICE"))
	switch svcSt {
	case "active", "running":
		fmt.Println(kv("Status", c("32", "● "+svcSt)))
	case "activating", "starting":
		fmt.Println(kv("Status", c("33", "◐ "+svcSt)))
	case "stopping":
		fmt.Println(kv("Status", c("33", "◑ "+svcSt)))
	default:
		if svcSt == "" {
			svcSt = "not installed"
		}
		fmt.Println(kv("Status", c("31", "○ "+svcSt)))
	}
	fmt.Println(kv("Version", cfg.AgentVersion))

	// ── AGENT ───────────────────────────────────────────────────────────────
	fmt.Println(sec("AGENT"))
	if s.IsEnrolled() {
		id := s.AgentID
		if len(id) > dashW-13 {
			id = id[:dashW-13-3] + "..."
		}
		fmt.Println(kv("ID", id))

		srv := cfg.ServerURL
		if len(srv) > dashW-13 {
			srv = srv[:dashW-13-3] + "..."
		}
		fmt.Println(kv("Server", srv))

		fmt.Println(kv("Enrolled",
			s.EnrolledAt.Format("2006-01-02")+
				c("2", "  ("+humanDur(now.Sub(s.EnrolledAt))+" ago)")))

		certLeft := time.Until(s.CertExpiresAt)
		certLine := s.CertExpiresAt.Format("2006-01-02") +
			c("2", "  ("+humanDays(certLeft)+" left)")
		switch {
		case certLeft < 7*24*time.Hour:
			fmt.Println(kv("Certificate", c("31", certLine)))
		case certLeft < 14*24*time.Hour:
			fmt.Println(kv("Certificate", c("33", certLine)))
		default:
			fmt.Println(kv("Certificate", c("32", certLine)))
		}

		if s.LastHeartbeatAt != nil {
			beatAge := now.Sub(*s.LastHeartbeatAt)
			beatLine := s.LastHeartbeatAt.Format("15:04:05") +
				c("2", "  ("+humanDur(beatAge)+" ago)")
			if beatAge > 2*time.Minute {
				fmt.Println(kv("Heartbeat", c("31", beatLine)))
			} else {
				fmt.Println(kv("Heartbeat", c("32", beatLine)))
			}
		} else {
			fmt.Println(kv("Heartbeat", c("33", "no data yet")))
		}
	} else {
		fmt.Println(dashRow(c("33", "Not enrolled.  Run: umbrella-agent setup")))
	}

	// ── METRICS ─────────────────────────────────────────────────────────────
	if snap != nil {
		fmt.Println(sec("METRICS"))

		const barW = 20
		cpuBar := metricBar(snap.CPUPercent, barW, ansi)
		fmt.Println(dashRow(
			c("2", "CPU   ") + cpuBar +
				fmt.Sprintf("  %5.1f%%", snap.CPUPercent)))

		var ramPct float64
		if snap.RAMTotalMB > 0 {
			ramPct = float64(snap.RAMUsedMB) / float64(snap.RAMTotalMB) * 100
		}
		ramBar := metricBar(ramPct, barW, ansi)
		fmt.Println(dashRow(
			c("2", "RAM   ") + ramBar +
				fmt.Sprintf("  %5.1f%%  %s/%s",
					ramPct, fmtMB(snap.RAMUsedMB), fmtMB(snap.RAMTotalMB))))

		var diskPct float64
		if snap.DiskTotalGB > 0 {
			diskPct = snap.DiskUsedGB / snap.DiskTotalGB * 100
		}
		diskBar := metricBar(diskPct, barW, ansi)
		fmt.Println(dashRow(
			c("2", "Disk  ") + diskBar +
				fmt.Sprintf("  %5.1f%%  %.0f/%.0f GB",
					diskPct, snap.DiskUsedGB, snap.DiskTotalGB)))
	}

	// ── ENFORCEMENT ─────────────────────────────────────────────────────────
	fmt.Println(sec("ENFORCEMENT"))
	es, _ := enforce.LoadEnforcementStatus(cfg.StateFile)
	if es == nil {
		fmt.Println(dashRow(c("2", "no data yet")))
	} else {
		if es.DNSSinkhole {
			fmt.Println(kv("DNS Sinkhole",
				c("32", fmt.Sprintf("● active    %d domains blocked", es.BlockedDomains))))
		} else {
			fmt.Println(kv("DNS Sinkhole", c("2", "○ inactive")))
		}
		if es.WFPFilters > 0 {
			fmt.Println(kv("WFP Filters",
				c("32", fmt.Sprintf("● active    %d IPs blocked", es.BlockedIPs))))
		} else {
			fmt.Println(kv("WFP Filters", c("2", "○ inactive")))
		}
		fmt.Println(kv("Updated",
			es.UpdatedAt.Local().Format("15:04:05")+
				c("2", "  ("+humanDur(time.Since(es.UpdatedAt))+" ago)")))
	}

	// ── POLICIES ────────────────────────────────────────────────────────────
	fmt.Println(sec("POLICIES"))
	ps, psErr := enforce.LoadState(cfg.StateFile)
	switch {
	case psErr != nil:
		fmt.Println(dashRow(c("31", "error: "+psErr.Error())))
	case ps == nil:
		fmt.Println(dashRow(c("2", "no data yet — agent has not polled the server")))
	default:
		age := time.Since(ps.AppliedAt)
		nPolicies := len(ps.Policies)
		policiesWord := "policies"
		if nPolicies == 1 {
			policiesWord = "policy"
		}
		updLine := "Updated " + ps.AppliedAt.Local().Format("15:04:05") +
			c("2", fmt.Sprintf("  (%s ago)   %d %s", humanDur(age), nPolicies, policiesWord))
		fmt.Println(dashRow(updLine))

		for _, p := range ps.Policies {
			name := p.Name
			if name == "" {
				name = p.ID
			}
			const nameW = 24
			if visLen(name) > nameW {
				name = string([]rune(name)[:nameW-3]) + "..."
			}

			var badge string
			if p.Action == "block" {
				badge = c("31", "✗ BLOCK")
			} else {
				badge = c("32", "✓ ALLOW")
			}

			var parts []string
			if p.Domains > 0 {
				parts = append(parts, fmt.Sprintf("%d dom", p.Domains))
			}
			if p.IPs > 0 {
				parts = append(parts, fmt.Sprintf("%d ip", p.IPs))
			}
			if p.Processes > 0 {
				parts = append(parts, fmt.Sprintf("%d proc", p.Processes))
			}
			rules := ""
			if len(parts) > 0 {
				rules = c("2", "  "+strings.Join(parts, " · "))
			}

			padName := name + strings.Repeat(" ", nameW-visLen(name))
			fmt.Println(dashRow(badge + "  " + padName + rules))
		}
	}

	// ── Footer ──────────────────────────────────────────────────────────────
	fmt.Println(dashBot())
	if hint != "" {
		fmt.Printf("  %s\n", c("2", hint))
	}
}

// ── Metric helpers ────────────────────────────────────────────────────────────

func metricBar(pct float64, width int, ansi bool) string {
	filled := int(pct / 100 * float64(width))
	if filled > width {
		filled = width
	}
	if filled < 0 {
		filled = 0
	}
	bar := strings.Repeat("█", filled) + strings.Repeat("░", width-filled)
	if !ansi {
		return bar
	}
	var code string
	switch {
	case pct >= 90:
		code = "31"
	case pct >= 75:
		code = "33"
	default:
		code = "32"
	}
	return "\033[" + code + "m" + bar + "\033[0m"
}

func fmtMB(mb int64) string {
	if mb >= 1024 {
		return fmt.Sprintf("%.1f GB", float64(mb)/1024)
	}
	return fmt.Sprintf("%d MB", mb)
}

// ── Time helpers ──────────────────────────────────────────────────────────────

func humanDur(d time.Duration) string {
	if d < 0 {
		d = -d
	}
	switch {
	case d < time.Minute:
		return fmt.Sprintf("%ds", int(d.Seconds()))
	case d < time.Hour:
		return fmt.Sprintf("%dm", int(d.Minutes()))
	case d < 24*time.Hour:
		return fmt.Sprintf("%dh %dm", int(d.Hours()), int(d.Minutes())%60)
	default:
		return fmt.Sprintf("%dd", int(d.Hours()/24))
	}
}

func humanDays(d time.Duration) string {
	days := int(d.Hours() / 24)
	if days == 1 {
		return "1 day"
	}
	return fmt.Sprintf("%d days", days)
}
