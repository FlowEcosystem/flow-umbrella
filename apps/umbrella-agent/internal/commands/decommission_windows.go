//go:build windows

package commands

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"syscall"
)

func decommission() Result {
	exe, err := os.Executable()
	if err != nil {
		return Result{Status: "failure", ErrMsg: "get exe path: " + err.Error()}
	}
	exe, _ = filepath.Abs(exe)
	dir := filepath.Dir(exe)

	// Script in %TEMP% so it can delete the installation directory itself.
	batPath := filepath.Join(os.TempDir(), "umbrella-decommission.bat")
	bat := "@echo off\r\n" +
		"ping 127.0.0.1 -n 6 > nul\r\n" +             // ~5s for agent to exit
		"sc stop UmbrellaAgent\r\n" +
		"ping 127.0.0.1 -n 4 > nul\r\n" +             // ~3s for process to release exe lock
		"sc delete UmbrellaAgent\r\n" +
		"icacls \"" + dir + "\" /reset /T /C /Q\r\n" + // reset ACLs so rd can proceed
		"rd /s /q \"" + dir + "\"\r\n" +
		"del /f /q \"%~f0\"\r\n"

	if err := os.WriteFile(batPath, []byte(bat), 0o755); err != nil {
		return Result{Status: "failure", ErrMsg: fmt.Sprintf("write decommission script: %v", err)}
	}

	cmd := exec.Command("cmd.exe", "/c", batPath)
	cmd.SysProcAttr = &syscall.SysProcAttr{
		CreationFlags: 0x08000000, // CREATE_NO_WINDOW
		HideWindow:    true,
	}
	if err := cmd.Start(); err != nil {
		return Result{Status: "failure", ErrMsg: fmt.Sprintf("start decommission script: %v", err)}
	}
	return Result{Status: "success", Output: jsonMsg("decommission script launched")}
}
