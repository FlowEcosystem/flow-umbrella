//go:build windows

package commands

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
)

func exeSuffix() string { return ".exe" }

// applyUpdate schedules a self-replace via a detached bat script.
//
// Flow:
//  1. Bat waits 5 s (service submits result + shuts down gracefully).
//  2. Bat stops the Windows service.
//  3. Bat waits 3 s for process to exit and release the exe lock.
//  4. Bat copies the new binary over the current exe.
//  5. Bat starts the service again.
func applyUpdate(newExePath string) error {
	exe, err := os.Executable()
	if err != nil {
		return fmt.Errorf("get exe path: %w", err)
	}
	exe, err = filepath.Abs(exe)
	if err != nil {
		return fmt.Errorf("abs exe path: %w", err)
	}

	bat := "@echo off\r\n" +
		"ping 127.0.0.1 -n 6 > nul\r\n" + // ~5 s delay
		"sc stop UmbrellaAgent\r\n" +
		"ping 127.0.0.1 -n 4 > nul\r\n" + // ~3 s for process to exit
		"copy /y \"" + newExePath + "\" \"" + exe + "\"\r\n" +
		"del /f /q \"" + newExePath + "\"\r\n" +
		"sc start UmbrellaAgent\r\n" +
		"del /f /q \"%~f0\"\r\n"

	batPath := filepath.Join(filepath.Dir(exe), "umbrella-update.bat")
	if err := os.WriteFile(batPath, []byte(bat), 0o755); err != nil {
		return fmt.Errorf("write update script: %w", err)
	}

	cmd := exec.Command("cmd.exe", "/c", batPath)
	cmd.SysProcAttr = &syscall.SysProcAttr{
		CreationFlags: 0x08000000, // CREATE_NO_WINDOW
		HideWindow:    true,
	}
	return cmd.Start() // detach; don't wait
}
