//go:build linux

package main

import (
	"fmt"
	"os"
	"os/exec"
	"strings"
)

const unitName = "umbrella-agent"
const unitPath = "/etc/systemd/system/umbrella-agent.service"

const unitTemplate = `[Unit]
Description=Umbrella Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=%s
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
`

// isServiceMode always returns false on Linux — the process is a normal
// foreground process managed by systemd; no in-process detection needed.
func isServiceMode() bool { return false }

// runAsService is never called on Linux (isServiceMode returns false),
// but must exist for compilation.
func runAsService(run func(<-chan struct{})) error {
	return fmt.Errorf("runAsService: not applicable on Linux (use systemd)")
}

func installService(cfgFile string) error {
	exePath := installedExePath()

	execStart := exePath + " run"
	if cfgFile != "" {
		execStart += " --config " + cfgFile
	}

	unit := fmt.Sprintf(unitTemplate, execStart)
	if err := os.WriteFile(unitPath, []byte(unit), 0o644); err != nil {
		return fmt.Errorf("write unit file (run as root): %w", err)
	}

	for _, args := range [][]string{
		{"daemon-reload"},
		{"enable", unitName},
	} {
		if out, err := systemctl(args...); err != nil {
			return fmt.Errorf("systemctl %s: %s: %w", strings.Join(args, " "), out, err)
		}
	}
	return nil
}

func uninstallService() error {
	_ = stopService()
	if out, err := systemctl("disable", unitName); err != nil {
		return fmt.Errorf("systemctl disable: %s: %w", out, err)
	}
	if err := os.Remove(unitPath); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("remove unit file: %w", err)
	}
	_, _ = systemctl("daemon-reload")
	return nil
}

func startService() error {
	out, err := systemctl("start", unitName)
	if err != nil {
		return fmt.Errorf("systemctl start: %s: %w", out, err)
	}
	return nil
}

func stopService() error {
	out, err := systemctl("stop", unitName)
	if err != nil {
		return fmt.Errorf("systemctl stop: %s: %w", out, err)
	}
	return nil
}

func serviceStatus() (string, error) {
	out, err := systemctl("is-active", unitName)
	status := strings.TrimSpace(out)
	if err != nil {
		if status == "inactive" || status == "unknown" {
			return status, nil
		}
		return status, nil
	}
	return status, nil
}

func systemctl(args ...string) (string, error) {
	out, err := exec.Command("systemctl", args...).CombinedOutput()
	return string(out), err
}
