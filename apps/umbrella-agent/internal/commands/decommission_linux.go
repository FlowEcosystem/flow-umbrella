//go:build linux

package commands

import (
	"fmt"
	"os"
	"os/exec"
	"syscall"
)

func decommission() Result {
	sh := "#!/bin/sh\n" +
		"sleep 5\n" +
		"systemctl disable --now umbrella-agent 2>/dev/null || true\n" +
		"rm -f '/etc/systemd/system/umbrella-agent.service'\n" +
		"systemctl daemon-reload 2>/dev/null || true\n" +
		"rm -f '/usr/local/bin/umbrella-agent'\n" +
		"rm -rf '/etc/umbrella-agent'\n" +
		"rm -rf '/var/lib/umbrella-agent'\n" +
		"rm -f '/var/log/umbrella-agent.log'\n" +
		"rm -f \"$0\"\n"

	shPath := "/tmp/umbrella-decommission.sh"
	if err := os.WriteFile(shPath, []byte(sh), 0o755); err != nil {
		return Result{Status: "failure", ErrMsg: fmt.Sprintf("write decommission script: %v", err)}
	}

	// Setsid detaches the script into its own session so systemd stopping
	// the parent service does not kill the cleanup process.
	cmd := exec.Command("/bin/sh", shPath)
	cmd.SysProcAttr = &syscall.SysProcAttr{Setsid: true}
	if err := cmd.Start(); err != nil {
		return Result{Status: "failure", ErrMsg: fmt.Sprintf("start decommission script: %v", err)}
	}
	return Result{Status: "success", Output: jsonMsg("decommission script launched")}
}
