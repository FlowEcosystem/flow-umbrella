package main

import (
	"bufio"
	"flag"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/flow-ecosystem/umbrella-agent/internal/agent"
	"github.com/flow-ecosystem/umbrella-agent/internal/config"
	"github.com/flow-ecosystem/umbrella-agent/internal/state"
)

const helpText = `Umbrella Agent

Usage:
  umbrella-agent [command] [--config <path>]

  Running without a command opens the interactive TUI menu.

Commands:
  (none)     Open interactive TUI (default)
  run        Run agent in the foreground (no service changes)
  setup      Enroll and install as a system service (non-interactive)
  monitor    Live status dashboard (standalone, no TUI)
  install    Install as a system service (host must already be enrolled)
  uninstall  Remove the system service
  start      Start the installed service
  stop       Stop the running service
  status     Print service status

Flags:
  --config <path>  Path to a JSON config file
`

func main() {
	// When the OS service manager (SCM / systemd) starts this binary, go
	// directly into managed-service mode without any CLI flag parsing.
	if isServiceMode() {
		if err := runManagedService(); err != nil {
			slog.Error("service run error", "err", err)
			os.Exit(1)
		}
		return
	}

	cmd, rest := splitCmd(os.Args[1:])

	fs := flag.NewFlagSet("umbrella-agent", flag.ExitOnError)
	cfgFile := fs.String("config", "", "path to JSON config file")
	_ = fs.Parse(rest)

	switch cmd {
	case "tui", "":
		runTUI(*cfgFile)
	case "setup":
		doSetup(*cfgFile)
	case "run":
		doRun(*cfgFile)
	case "monitor":
		doMonitor(*cfgFile)
	case "install":
		doInstall(*cfgFile)
	case "uninstall":
		doUninstall()
	case "start":
		doStart()
	case "stop":
		doStop()
	case "status":
		doStatus()
	case "help":
		fmt.Print(helpText)
	default:
		fmt.Fprintf(os.Stderr, "unknown command: %q\n\n%s", cmd, helpText)
		os.Exit(1)
	}
}

// splitCmd returns the subcommand and the remaining args.
// Defaults to "tui" (interactive mode) when no subcommand is given.
func splitCmd(args []string) (string, []string) {
	if len(args) == 0 || args[0] == "" || args[0][0] == '-' {
		return "tui", args
	}
	return args[0], args[1:]
}

// ── Subcommand handlers ───────────────────────────────────────────────────────

func doSetup(cfgFile string) {
	pauseOnExit = true // keep the window open on both success and error

	cfg, err := config.Load(cfgFile)
	if err != nil {
		fatalf("load config: %v", err)
	}
	s, err := state.Load(cfg.StateFile)
	if err != nil {
		fatalf("load state: %v", err)
	}

	if !s.IsEnrolled() {
		cfgFile = runWizard(&cfg, s, cfgFile)
	} else {
		fmt.Printf("Already enrolled as agent %s.\n\n", s.AgentID)
	}

	doInstall(cfgFile)

	waitForEnter()
}

func doRun(cfgFile string) {
	cfg, err := config.Load(cfgFile)
	if err != nil {
		fatalf("load config: %v", err)
	}
	if cfg.ServerURL == "" {
		fatalf("server_url is required (config file or UMBRELLA_SERVER_URL env)")
	}
	s, err := state.Load(cfg.StateFile)
	if err != nil {
		fatalf("load state: %v", err)
	}

	a := agent.New(cfg, s)
	if !s.IsEnrolled() {
		if err := a.Enroll(); err != nil {
			fatalf("enrollment: %v", err)
		}
	} else {
		slog.Info("already enrolled", "agent_id", s.AgentID)
	}

	done := make(chan struct{})
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
	go func() { <-ch; close(done) }()
	a.Run(done)
}

func doInstall(cfgFile string) {
	fmt.Print("Installing service... ")
	if err := installService(cfgFile); err != nil {
		fmt.Println("FAILED")
		fatalf("install service: %v", err)
	}
	fmt.Println("OK")

	fmt.Print("Starting service...   ")
	if err := startService(); err != nil {
		fmt.Println("FAILED")
		fatalf("start service: %v", err)
	}
	fmt.Println("OK")
	fmt.Println("\nAgent is running as a background service.")
}

func doUninstall() {
	fmt.Print("Stopping service...    ")
	_ = stopService()
	fmt.Println("OK")

	fmt.Print("Uninstalling service... ")
	if err := uninstallService(); err != nil {
		fmt.Println("FAILED")
		fatalf("uninstall: %v", err)
	}
	fmt.Println("OK")
	fmt.Println("Service removed.")
}

func doStart() {
	if err := startService(); err != nil {
		fatalf("start service: %v", err)
	}
	fmt.Println("Service started.")
}

func doStop() {
	if err := stopService(); err != nil {
		fatalf("stop service: %v", err)
	}
	fmt.Println("Service stopped.")
}

func doStatus() {
	st, err := serviceStatus()
	if err != nil {
		fatalf("status: %v", err)
	}
	fmt.Printf("Service: %s\n", st)
}

// runManagedService is called when the OS service manager starts the binary.
// It loads config from a well-known location and runs the agent loop.
func runManagedService() error {
	cfgFile := managedConfigFile()
	cfg, err := config.Load(cfgFile)
	if err != nil {
		return fmt.Errorf("load config: %w", err)
	}
	s, err := state.Load(cfg.StateFile)
	if err != nil {
		return fmt.Errorf("load state: %w", err)
	}
	a := agent.New(cfg, s)
	if !s.IsEnrolled() {
		if err := a.Enroll(); err != nil {
			return fmt.Errorf("enrollment: %w", err)
		}
	}
	return runAsService(a.Run)
}

// managedConfigFile returns the platform-default config path used when the
// service manager starts the binary (no CLI flags available).
func managedConfigFile() string {
	return config.DefaultConfigFile()
}

// pauseOnExit is set to true for interactive commands (setup) so the console
// window doesn't close before the user can read the output.
var pauseOnExit bool

func waitForEnter() {
	fmt.Print("\nPress Enter to exit...")
	bufio.NewReader(os.Stdin).ReadString('\n') //nolint:errcheck
}

func fatalf(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "\n  error: "+format+"\n", args...)
	if pauseOnExit {
		waitForEnter()
	}
	os.Exit(1)
}
