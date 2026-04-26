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
	"github.com/flow-ecosystem/umbrella-agent/internal/state"
)

const autoRefresh = 3 * time.Second

func doMonitor(cfgFile string) {
	cfg, err := config.Load(cfgFile)
	if err != nil {
		fatalf("load config: %v", err)
	}

	fd := int(os.Stdin.Fd())

	if !term.IsTerminal(fd) {
		s, _ := state.Load(cfg.StateFile)
		svcSt, _ := serviceStatus()
		renderDashboard(cfg, s, svcSt, false, "Press Ctrl+C to exit")
		return
	}

	oldState, err := term.MakeRaw(fd)
	if err != nil {
		s, _ := state.Load(cfg.StateFile)
		svcSt, _ := serviceStatus()
		renderDashboard(cfg, s, svcSt, false, "Press Ctrl+C to exit")
		return
	}
	defer term.Restore(fd, oldState)
	defer fmt.Print("\033[?25h\033[2J\033[H") // show cursor + clear on exit

	fmt.Print("\033[?25l") // hide cursor while running

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
			case 'q', 'Q', 3: // 3 = Ctrl+C in raw mode
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

// renderDashboard prints the status dashboard.
// ansi=true enables colours and in-place screen refresh.
// hint is the footer help line (caller-supplied so TUI can show "back" instead of "quit").
func renderDashboard(cfg config.Config, s *state.State, svcSt string, ansi bool, hint string) { //nolint:cyclop
	now := time.Now()

	clr := func(code, text string) string {
		if !ansi {
			return text
		}
		return "\033[" + code + "m" + text + "\033[0m"
	}

	const w = 54
	sep := "  " + strings.Repeat("─", w)

	if ansi {
		fmt.Print("\033[2J\033[H")
	}

	// ── Header ──────────────────────────────────────────────
	title := "UMBRELLA AGENT MONITOR"
	ts := now.Format("15:04:05")
	pad := w - len(title) - len(ts)
	if pad < 1 {
		pad = 1
	}
	fmt.Printf("  %s%s%s\n", clr("1", title), strings.Repeat(" ", pad), ts)
	fmt.Println(sep)
	fmt.Println()

	// ── Service ──────────────────────────────────────────────
	fmt.Printf("  %s\n", clr("1", "SERVICE"))
	switch svcSt {
	case "active", "running":
		fmt.Printf("    Status:      %s\n", clr("32", "● "+svcSt))
	case "activating", "starting", "stopping":
		fmt.Printf("    Status:      %s\n", clr("33", "◐ "+svcSt))
	default:
		if svcSt == "" {
			svcSt = "unknown"
		}
		fmt.Printf("    Status:      %s\n", clr("31", "○ "+svcSt))
	}
	fmt.Println()

	// ── Agent ────────────────────────────────────────────────
	fmt.Printf("  %s\n", clr("1", "AGENT"))
	if s.IsEnrolled() {
		fmt.Printf("    ID:          %s\n", s.AgentID)
		fmt.Printf("    Server:      %s\n", cfg.ServerURL)
		fmt.Printf("    Enrolled:    %s  (%s ago)\n",
			s.EnrolledAt.Format("2006-01-02"),
			humanDur(now.Sub(s.EnrolledAt)),
		)

		certLeft := time.Until(s.CertExpiresAt)
		certStr := fmt.Sprintf("expires %s  (%s left)",
			s.CertExpiresAt.Format("2006-01-02"),
			humanDays(certLeft),
		)
		switch {
		case certLeft < 7*24*time.Hour:
			certStr = clr("31", certStr)
		case certLeft < 14*24*time.Hour:
			certStr = clr("33", certStr)
		default:
			certStr = clr("32", certStr)
		}
		fmt.Printf("    Certificate: %s\n", certStr)

		if s.LastHeartbeatAt != nil {
			beatAge := now.Sub(*s.LastHeartbeatAt)
			beatStr := fmt.Sprintf("%s  (%s ago)",
				s.LastHeartbeatAt.Format("15:04:05"),
				humanDur(beatAge),
			)
			if beatAge > 2*time.Minute {
				beatStr = clr("31", beatStr)
			} else {
				beatStr = clr("32", beatStr)
			}
			fmt.Printf("    Last beat:   %s\n", beatStr)
		} else {
			fmt.Printf("    Last beat:   %s\n", clr("33", "unknown  (agent not yet running)"))
		}
	} else {
		fmt.Printf("    %s\n", clr("33", "Not enrolled. Run:  umbrella-agent setup"))
	}
	fmt.Println()

	// ── Polling ──────────────────────────────────────────────
	fmt.Printf("  %s\n", clr("1", "POLLING"))
	cmdSec := cfg.CommandPollIntervalSec
	if s.CommandPollIntervalSec > 0 {
		cmdSec = s.CommandPollIntervalSec
	}
	polSec := cfg.PolicyPollIntervalSec
	if s.PolicyPollIntervalSec > 0 {
		polSec = s.PolicyPollIntervalSec
	}
	fmt.Printf("    Commands:    every %ds\n", cmdSec)
	fmt.Printf("    Policies:    every %ds\n", polSec)
	fmt.Printf("    Heartbeat:   every %ds\n", cfg.HeartbeatIntervalSec)
	fmt.Println()

	// ── Enforcement ──────────────────────────────────────────
	fmt.Printf("  %s\n", clr("1", "ENFORCEMENT"))
	es, _ := enforce.LoadEnforcementStatus(cfg.StateFile)
	if es == nil {
		fmt.Printf("    %s\n", clr("33", "нет данных"))
	} else {
		if es.DNSSinkhole {
			fmt.Printf("    DNS синкхол: %s  (%d доменов)\n",
				clr("32", "● active"), es.BlockedDomains)
		} else {
			fmt.Printf("    DNS синкхол: %s\n", clr("2", "○ inactive"))
		}
		if es.WFPFilters > 0 {
			fmt.Printf("    WFP фильтры: %s  (%d IP)\n",
				clr("32", "● active"), es.BlockedIPs)
		} else {
			fmt.Printf("    WFP фильтры: %s\n", clr("2", "○ inactive"))
		}
		fmt.Printf("    Обновлено:   %s (%s назад)\n",
			es.UpdatedAt.Local().Format("15:04:05"),
			humanDur(time.Since(es.UpdatedAt)))
	}
	fmt.Println()

	// ── Policies ─────────────────────────────────────────────
	fmt.Printf("  %s\n", clr("1", "ПОЛИТИКИ"))
	ps, psErr := enforce.LoadState(cfg.StateFile)
	switch {
	case psErr != nil:
		fmt.Printf("    %s\n", clr("31", "Ошибка чтения: "+psErr.Error()))
		fmt.Printf("    %s\n", clr("2", enforce.PolicyStatePath(cfg.StateFile)))
	case ps == nil:
		fmt.Printf("    %s\n", clr("33", "нет данных — агент ещё не опросил сервер"))
		fmt.Printf("    %s\n", clr("2", enforce.PolicyStatePath(cfg.StateFile)))
	case len(ps.Policies) == 0:
		age := time.Since(ps.AppliedAt)
		fmt.Printf("    Обновлено: %s (%s назад)\n",
			ps.AppliedAt.Local().Format("15:04:05"), humanDur(age))
		fmt.Printf("    %s\n", clr("2", "политик нет"))
	default:
		age := time.Since(ps.AppliedAt)
		fmt.Printf("    Обновлено: %s (%s назад)   всего: %d\n",
			ps.AppliedAt.Local().Format("15:04:05"), humanDur(age), len(ps.Policies))
		for _, p := range ps.Policies {
			var badge string
			if p.Action == "block" {
				badge = clr("31", "✗ block")
			} else {
				badge = clr("32", "✓ allow")
			}
			name := p.Name
			if name == "" {
				name = p.ID
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
			rulesStr := ""
			if len(parts) > 0 {
				rulesStr = "  " + clr("2", strings.Join(parts, " · "))
			}
			fmt.Printf("    %s  %-28s%s\n", badge, name, rulesStr)
		}
	}
	fmt.Println()

	fmt.Println(sep)
	if ansi {
		fmt.Printf("  %s\n", clr("2", hint))
	} else {
		fmt.Printf("  Press Ctrl+C to exit\n")
	}
}

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
