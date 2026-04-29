//go:build windows

package main

import (
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"

	"golang.org/x/sys/windows/registry"
)

const agentExeName = "umbrella-agent.exe"

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

func installedExePath() string {
	return filepath.Join(installDir(), agentExeName)
}

// copyToInstallDir copies the running executable to %ProgramFiles%\UmbrellaAgent\.
// No-op if already running from there.
func copyToInstallDir() error {
	src, err := os.Executable()
	if err != nil {
		return fmt.Errorf("get exe path: %w", err)
	}
	src, _ = filepath.Abs(src)
	dst := installedExePath()

	if strings.EqualFold(src, dst) {
		return nil
	}

	if err := os.MkdirAll(installDir(), 0o755); err != nil {
		return fmt.Errorf("create install dir: %w", err)
	}

	in, err := os.Open(src)
	if err != nil {
		return fmt.Errorf("open source exe: %w", err)
	}
	defer in.Close()

	out, err := os.Create(dst)
	if err != nil {
		return fmt.Errorf("create target exe: %w", err)
	}
	defer out.Close()

	if _, err := io.Copy(out, in); err != nil {
		return fmt.Errorf("copy exe: %w", err)
	}
	return out.Sync()
}

const regEnvKey = `SYSTEM\CurrentControlSet\Control\Session Manager\Environment`

// addToSystemPath appends installDir() to the machine-level PATH (registry).
func addToSystemPath() error {
	k, err := registry.OpenKey(registry.LOCAL_MACHINE, regEnvKey,
		registry.QUERY_VALUE|registry.SET_VALUE)
	if err != nil {
		return fmt.Errorf("open registry: %w", err)
	}
	defer k.Close()

	cur, _, err := k.GetStringValue("Path")
	if err != nil {
		return fmt.Errorf("read PATH: %w", err)
	}

	dir := installDir()
	for _, p := range strings.Split(cur, ";") {
		if strings.EqualFold(strings.TrimSpace(p), dir) {
			return nil // already present
		}
	}

	newPath := strings.TrimRight(cur, ";") + ";" + dir
	return k.SetStringValue("Path", newPath)
}

// removeFromSystemPath removes installDir() from the machine-level PATH (registry).
func removeFromSystemPath() error {
	k, err := registry.OpenKey(registry.LOCAL_MACHINE, regEnvKey,
		registry.QUERY_VALUE|registry.SET_VALUE)
	if err != nil {
		return fmt.Errorf("open registry: %w", err)
	}
	defer k.Close()

	cur, _, err := k.GetStringValue("Path")
	if err != nil {
		return fmt.Errorf("read PATH: %w", err)
	}

	dir := installDir()
	parts := strings.Split(cur, ";")
	kept := parts[:0]
	for _, p := range parts {
		if !strings.EqualFold(strings.TrimSpace(p), dir) {
			kept = append(kept, p)
		}
	}

	return k.SetStringValue("Path", strings.Join(kept, ";"))
}

// launchCleanupScript writes and starts a bat that — after a short delay so
// the current process can exit — deletes both the install dir and data dir.
func launchCleanupScript() error {
	idir := installDir()
	ddir := dataDir()

	batPath := filepath.Join(os.TempDir(), "umbrella-cleanup.bat")
	bat := "@echo off\r\n" +
		"ping 127.0.0.1 -n 4 > nul\r\n" + // ~3 s — wait for this process to exit
		"rd /s /q \"" + idir + "\"\r\n" +
		"rd /s /q \"" + ddir + "\"\r\n" +
		"del /f /q \"%~f0\"\r\n"

	if err := os.WriteFile(batPath, []byte(bat), 0o755); err != nil {
		return fmt.Errorf("write cleanup script: %w", err)
	}
	return launchDetached("cmd.exe", "/c", batPath)
}

// launchDetached starts a process fully detached (CREATE_NO_WINDOW) so it
// survives after the current process exits.
func launchDetached(name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.SysProcAttr = &syscall.SysProcAttr{
		CreationFlags: 0x08000000, // CREATE_NO_WINDOW
		HideWindow:    true,
	}
	return cmd.Start()
}
