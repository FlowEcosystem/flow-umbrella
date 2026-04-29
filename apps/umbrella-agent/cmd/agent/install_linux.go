//go:build linux

package main

import (
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
)

const agentExeName = "umbrella-agent"

func installDir() string       { return "/usr/local/bin" }
func dataDir() string          { return "/var/lib/umbrella-agent" }
func installedExePath() string { return filepath.Join(installDir(), agentExeName) }

func copyToInstallDir() error {
	src, err := os.Executable()
	if err != nil {
		return fmt.Errorf("get exe path: %w", err)
	}
	src, _ = filepath.Abs(src)
	dst := installedExePath()

	if src == dst {
		return nil
	}

	in, err := os.Open(src)
	if err != nil {
		return fmt.Errorf("open source exe: %w", err)
	}
	defer in.Close()

	out, err := os.Create(dst)
	if err != nil {
		return fmt.Errorf("create target exe (run as root): %w", err)
	}
	defer out.Close()

	if _, err := io.Copy(out, in); err != nil {
		return fmt.Errorf("copy exe: %w", err)
	}
	if err := out.Sync(); err != nil {
		return err
	}
	return os.Chmod(dst, 0o755)
}

// addToSystemPath is a no-op on Linux — /usr/local/bin is already in PATH.
func addToSystemPath() error    { return nil }
func removeFromSystemPath() error { return nil }

func launchCleanupScript() error {
	sh := "#!/bin/sh\n" +
		"sleep 5\n" +
		"rm -f '/usr/local/bin/umbrella-agent'\n" +
		"rm -f '/etc/systemd/system/umbrella-agent.service'\n" +
		"systemctl daemon-reload 2>/dev/null || true\n" +
		"rm -rf '/etc/umbrella-agent'\n" +
		"rm -rf '/var/lib/umbrella-agent'\n" +
		"rm -f '/var/log/umbrella-agent.log'\n" +
		"rm -f \"$0\"\n"

	shPath := "/tmp/umbrella-cleanup.sh"
	if err := os.WriteFile(shPath, []byte(sh), 0o755); err != nil {
		return fmt.Errorf("write cleanup script: %w", err)
	}

	cmd := exec.Command("/bin/sh", shPath)
	return cmd.Start()
}
