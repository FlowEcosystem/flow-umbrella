//go:build windows

package main

import (
	"os"

	"golang.org/x/sys/windows"
)

// enableANSI turns on ANSI escape-code processing for stdout on Windows.
// Without this, terminals like cmd.exe print raw escape sequences instead of
// rendering colours and cursor movement.
func enableANSI() {
	h := windows.Handle(os.Stdout.Fd())
	var mode uint32
	if windows.GetConsoleMode(h, &mode) != nil {
		return
	}
	const enableVirtualTerminalProcessing = 0x0004
	_ = windows.SetConsoleMode(h, mode|enableVirtualTerminalProcessing)
}
