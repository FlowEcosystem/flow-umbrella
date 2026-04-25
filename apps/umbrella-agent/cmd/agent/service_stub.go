//go:build !windows && !linux

package main

import "fmt"

func isServiceMode() bool { return false }

func runAsService(_ func(<-chan struct{})) error {
	return fmt.Errorf("service management is not supported on this platform")
}

func installService(_ string) error {
	return fmt.Errorf("service management is not supported on this platform")
}

func uninstallService() error {
	return fmt.Errorf("service management is not supported on this platform")
}

func startService() error {
	return fmt.Errorf("service management is not supported on this platform")
}

func stopService() error {
	return fmt.Errorf("service management is not supported on this platform")
}

func serviceStatus() (string, error) {
	return "unsupported platform", nil
}
