//go:build !windows

package commands

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

func exeSuffix() string { return "" }

// applyUpdate schedules a self-replace via a detached shell script.
//
// Flow:
//  1. Script waits 3 s (service submits result, systemd begins restart).
//  2. Script copies the new binary over the current exe.
//  3. Script triggers a systemd service restart.
func applyUpdate(newExePath string) error {
	exe, err := os.Executable()
	if err != nil {
		return fmt.Errorf("get exe path: %w", err)
	}
	exe, err = filepath.Abs(exe)
	if err != nil {
		return fmt.Errorf("abs exe path: %w", err)
	}

	sh := "#!/bin/sh\n" +
		"sleep 3\n" +
		"cp -f '" + newExePath + "' '" + exe + "'\n" +
		"chmod +x '" + exe + "'\n" +
		"rm -f '" + newExePath + "'\n" +
		"systemctl restart umbrella-agent\n" +
		"rm -f \"$0\"\n"

	shPath := filepath.Join(filepath.Dir(exe), "umbrella-update.sh")
	if err := os.WriteFile(shPath, []byte(sh), 0o755); err != nil {
		return fmt.Errorf("write update script: %w", err)
	}

	cmd := exec.Command("/bin/sh", shPath)
	return cmd.Start() // detach; don't wait
}
