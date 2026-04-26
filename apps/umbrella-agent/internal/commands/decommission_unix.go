//go:build !windows

package commands

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

func decommission() Result {
	exe, err := os.Executable()
	if err != nil {
		return Result{Status: "failure", ErrMsg: "get exe path: " + err.Error()}
	}
	exe, _ = filepath.Abs(exe)
	dir := filepath.Dir(exe)

	shPath := "/tmp/umbrella-decommission.sh"
	sh := "#!/bin/sh\n" +
		"sleep 5\n" +
		"systemctl disable --now umbrella-agent 2>/dev/null || true\n" +
		"rm -rf '" + dir + "'\n" +
		"rm -f \"$0\"\n"

	if err := os.WriteFile(shPath, []byte(sh), 0o755); err != nil {
		return Result{Status: "failure", ErrMsg: fmt.Sprintf("write decommission script: %v", err)}
	}

	cmd := exec.Command("/bin/sh", shPath)
	if err := cmd.Start(); err != nil {
		return Result{Status: "failure", ErrMsg: fmt.Sprintf("start decommission script: %v", err)}
	}
	return Result{Status: "success", Output: jsonMsg("decommission script launched")}
}
