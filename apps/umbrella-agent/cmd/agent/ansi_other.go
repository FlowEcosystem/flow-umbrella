//go:build !windows

package main

func enableANSI() {} // ANSI is supported by default on Linux/macOS terminals.
