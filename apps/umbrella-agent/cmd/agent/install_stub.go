//go:build !windows && !linux

package main

func installDir() string      { return "" }
func dataDir() string         { return "" }
func installedExePath() string { return "" }
func copyToInstallDir() error  { return nil }
func addToSystemPath() error   { return nil }
func removeFromSystemPath() error { return nil }
func launchCleanupScript() error  { return nil }
