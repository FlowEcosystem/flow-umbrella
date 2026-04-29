package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"log/slog"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"

	"github.com/flow-ecosystem/umbrella-agent/internal/agent"
	"github.com/flow-ecosystem/umbrella-agent/internal/config"
	"github.com/flow-ecosystem/umbrella-agent/internal/state"
	"github.com/flow-ecosystem/umbrella-agent/internal/token"
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
  --config <path>   Path to a JSON config file
  --token  <token>  Offline decommission token (for uninstall when server is unavailable)
                    Generate via: management console → Agents → Offline decommission token
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
	offlineToken := fs.String("token", "", "offline decommission token")
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
		doUninstall(*cfgFile, *offlineToken)
	case "start":
		doStart()
	case "stop":
		doStop(*cfgFile)
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

// initLogging sets up slog to write to the log file (primary) and stdout.
// Returns a closer for the file; call defer on it.
func initLogging(logFile string) io.Closer {
	opts := &slog.HandlerOptions{Level: slog.LevelInfo}
	var w io.Writer = os.Stdout
	var closer io.Closer = io.NopCloser(nil)

	if logFile != "" {
		if err := os.MkdirAll(filepath.Dir(logFile), 0o755); err == nil {
			if f, err := os.OpenFile(logFile, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o644); err == nil {
				// File is first: io.MultiWriter writes in order and stops on the
				// first error. On Windows the service has a null stdout handle —
				// writing to it fails — so file must come before stdout to ensure
				// logs always reach the file even when stdout is unavailable.
				w = io.MultiWriter(f, &noerrWriter{os.Stdout})
				closer = f
			}
		}
	}

	slog.SetDefault(slog.New(slog.NewTextHandler(w, opts)))
	return closer
}

// noerrWriter wraps a writer and always reports a successful write.
// This prevents io.MultiWriter from aborting the chain when stdout is
// unavailable (e.g. null handle on a Windows SCM service).
type noerrWriter struct{ w io.Writer }

func (n *noerrWriter) Write(p []byte) (int, error) {
	n.w.Write(p) //nolint:errcheck
	return len(p), nil
}

func doRun(cfgFile string) {
	cfg, err := config.Load(cfgFile)
	if err != nil {
		fatalf("load config: %v", err)
	}
	closer := initLogging(cfg.LogFile)
	defer closer.Close()

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
	fmt.Print("Installing executable...    ")
	if err := copyToInstallDir(); err != nil {
		fmt.Println("FAILED")
		fatalf("copy to install dir: %v", err)
	}
	fmt.Println("OK")

	fmt.Print("Adding to system PATH...    ")
	if err := addToSystemPath(); err != nil {
		fmt.Printf("warning: %v\n", err)
	} else {
		fmt.Println("OK")
	}

	fmt.Print("Installing service...       ")
	if err := installService(cfgFile); err != nil {
		fmt.Println("FAILED")
		fatalf("install service: %v", err)
	}
	fmt.Println("OK")

	fmt.Print("Starting service...         ")
	if err := startService(); err != nil {
		fmt.Println("FAILED")
		fatalf("start service: %v", err)
	}
	fmt.Println("OK")
	fmt.Println("\nAgent is running as a background service.")
	fmt.Println("You can now run 'umbrella-agent' from any terminal (open a new window).")
}

func doUninstall(cfgFile, offlineToken string) {
	if agentIsEnrolled(cfgFile) {
		if offlineToken != "" && verifyOfflineToken(cfgFile, offlineToken) {
			fmt.Println("Offline token verified. Proceeding with decommission.")
		} else if offlineToken != "" {
			fmt.Fprintln(os.Stderr, "\n  error: invalid or expired offline token.")
			fmt.Fprintln(os.Stderr, "  Generate a fresh token via: management console → Agents → Offline decommission token")
			os.Exit(1)
		} else {
			fmt.Fprintln(os.Stderr, "\n  Agent is enrolled and tamper-protected.")
			fmt.Fprintln(os.Stderr, "  To remove: open the management console → Agents → Decommission.")
			fmt.Fprintln(os.Stderr, "  The agent will uninstall itself upon receiving the server command.")
			fmt.Fprintln(os.Stderr, "  If the server is unavailable, use: umbrella-agent uninstall --token <offline-token>")
			os.Exit(1)
		}
	}

	fmt.Print("Stopping service...         ")
	_ = stopService()
	fmt.Println("OK")

	fmt.Print("Uninstalling service...     ")
	if err := uninstallService(); err != nil {
		fmt.Println("FAILED")
		fatalf("uninstall: %v", err)
	}
	fmt.Println("OK")

	fmt.Print("Removing from PATH...       ")
	if err := removeFromSystemPath(); err != nil {
		fmt.Printf("warning: %v\n", err)
	} else {
		fmt.Println("OK")
	}

	fmt.Print("Scheduling file cleanup...  ")
	if err := launchCleanupScript(); err != nil {
		fmt.Printf("warning: manual cleanup required: %v\n", err)
	} else {
		fmt.Println("OK")
	}

	fmt.Println("\nAgent removed. Files will be deleted in a few seconds.")
	fmt.Println("Open a new terminal window for PATH changes to take effect.")
}

func doStart() {
	if err := startService(); err != nil {
		fatalf("start service: %v", err)
	}
	fmt.Println("Service started.")
}

func doStop(cfgFile string) {
	if agentIsEnrolled(cfgFile) {
		fmt.Fprintln(os.Stderr, "\n  Agent is enrolled and tamper-protected.")
		fmt.Fprintln(os.Stderr, "  Service cannot be stopped manually. Use the management console.")
		os.Exit(1)
	}
	if err := stopService(); err != nil {
		fatalf("stop service: %v", err)
	}
	fmt.Println("Service stopped.")
}

// agentIsEnrolled returns true if a valid state file exists with an agent ID.
func agentIsEnrolled(cfgFile string) bool {
	cfg, err := config.Load(cfgFile)
	if err != nil {
		return false
	}
	s, err := state.Load(cfg.StateFile)
	if err != nil {
		return false
	}
	return s.IsEnrolled()
}

// verifyOfflineToken checks an admin-supplied offline decommission token.
// The token is a base64url-encoded ECDSA P-256 signature over SHA-256 of
// "decommission:{agentID}:{dayStamp}", verified with the public key stored at enrollment.
func verifyOfflineToken(cfgFile, tok string) bool {
	cfg, err := config.Load(cfgFile)
	if err != nil {
		return false
	}
	s, err := state.Load(cfg.StateFile)
	if err != nil || !s.IsEnrolled() {
		return false
	}
	return token.Validate(s.DecommissionPublicKey, s.AgentID, tok)
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
	closer := initLogging(cfg.LogFile)
	defer closer.Close()

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
