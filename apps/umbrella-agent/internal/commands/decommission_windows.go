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
	idir := installDir()
	ddir := dataDir()

	batPath := filepath.Join(os.TempDir(), "umbrella-decommission.bat")
	bat := "@echo off\r\n" +
		"ping 127.0.0.1 -n 6 > nul\r\n" + // ~5s — agent exits
		"sc.exe stop UmbrellaAgent\r\n" +
		"ping 127.0.0.1 -n 4 > nul\r\n" + // ~3s — process releases exe lock
		"sc.exe delete UmbrellaAgent\r\n" +
		// Remove install dir from system PATH via PowerShell.
		"powershell -NoProfile -NonInteractive -Command " +
		"\"$p=([Environment]::GetEnvironmentVariable('Path','Machine') -split ';'" +
		" | Where-Object {$_ -notlike '*UmbrellaAgent*'}) -join ';';" +
		"[Environment]::SetEnvironmentVariable('Path',$p,'Machine')\"\r\n" +
		"rd /s /q \"" + idir + "\"\r\n" +
		"rd /s /q \"" + ddir + "\"\r\n" +
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

func installDir() string {
	pf := os.Getenv("ProgramFiles")
	if pf == "" {
		pf = `C:\Program Files`
	}
	return filepath.Join(pf, "UmbrellaAgent")
}

func dataDir() string {
	pd := os.Getenv("PROGRAMDATA")
	if pd == "" {
		pd = `C:\ProgramData`
	}
	return filepath.Join(pd, "UmbrellaAgent")
}
