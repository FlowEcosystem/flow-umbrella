package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/flow-ecosystem/umbrella-agent/internal/agent"
	"github.com/flow-ecosystem/umbrella-agent/internal/config"
	"github.com/flow-ecosystem/umbrella-agent/internal/state"
)

// runWizard prompts for missing config values, enrolls the agent, saves the
// config (minus the one-time token) next to the executable, and returns the
// path of the written config file.
func runWizard(cfg *config.Config, s *state.State, cfgFile string) string {
	r := bufio.NewReader(os.Stdin)

	fmt.Println("  ╔═══════════════════════════════╗")
	fmt.Println("  ║   Umbrella Agent — Setup      ║")
	fmt.Println("  ╚═══════════════════════════════╝")
	fmt.Println()

	if cfg.ServerURL == "" {
		fmt.Print("  Server URL (e.g. api.umbrella.su:8443): ")
		line, _ := r.ReadString('\n')
		cfg.ServerURL = strings.TrimSpace(line)
		if cfg.ServerURL == "" {
			fatalf("server URL is required")
		}
	} else {
		fmt.Printf("  Server URL:       %s\n", cfg.ServerURL)
	}

	fmt.Print("  Enrollment Token: ")
	line, _ := r.ReadString('\n')
	cfg.EnrollmentToken = strings.TrimSpace(line)
	if cfg.EnrollmentToken == "" {
		fatalf("enrollment token is required")
	}

	fmt.Print("  Пропустить TLS-проверку? [y/N]: ")
	line, _ = r.ReadString('\n')
	if strings.ToLower(strings.TrimSpace(line)) == "y" {
		cfg.InsecureSkipVerify = true
	}

	fmt.Println()
	fmt.Print("  Enrolling...       ")
	os.Stdout.Sync()

	a := agent.New(*cfg, s)
	if err := a.Enroll(); err != nil {
		fmt.Println("FAILED")
		fatalf("enrollment: %v", err)
	}
	fmt.Println("OK")

	// Persist config (without the token — it's single-use) so the managed
	// service can find the server URL on every restart.
	out := writeConfig(cfg, cfgFile)
	if out != "" {
		fmt.Printf("  Config saved:      %s\n", out)
	}

	fmt.Println()
	return out
}

// writeConfig marshals cfg (without the enrollment token) to disk.
// If cfgFile is empty it uses the platform default path.
func writeConfig(cfg *config.Config, cfgFile string) string {
	if cfgFile == "" {
		cfgFile = config.DefaultConfigFile()
	}

	if err := os.MkdirAll(filepath.Dir(cfgFile), 0o700); err != nil {
		fmt.Fprintf(os.Stderr, "  warning: create config dir: %v\n", err)
		return ""
	}

	// Don't persist the token — it was single-use for enrollment.
	saved := *cfg
	saved.EnrollmentToken = ""

	b, err := json.MarshalIndent(saved, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "  warning: marshal config: %v\n", err)
		return ""
	}
	if err := os.WriteFile(cfgFile, b, 0o600); err != nil {
		fmt.Fprintf(os.Stderr, "  warning: write config: %v\n", err)
		return ""
	}
	return cfgFile
}
