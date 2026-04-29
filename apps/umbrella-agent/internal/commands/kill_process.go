package commands

import (
	"encoding/json"
	"fmt"
	"os/exec"
	"runtime"
)

func killProcess(payload json.RawMessage) Result {
	var p struct {
		Name string `json:"name"`
	}
	if err := json.Unmarshal(payload, &p); err != nil || p.Name == "" {
		return Result{Status: "failure", ErrMsg: "kill_process: missing or invalid name"}
	}

	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		cmd = exec.Command("taskkill", "/F", "/IM", p.Name)
	case "linux", "darwin":
		cmd = exec.Command("pkill", "-9", "-x", p.Name)
	default:
		return Result{Status: "failure", ErrMsg: "kill_process: unsupported OS"}
	}

	if out, err := cmd.CombinedOutput(); err != nil {
		return Result{
			Status: "failure",
			ErrMsg: fmt.Sprintf("kill_process %s: %v: %s", p.Name, err, string(out)),
		}
	}
	return Result{Status: "success", Output: jsonMsg(fmt.Sprintf("killed: %s", p.Name))}
}
