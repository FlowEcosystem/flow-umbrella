package commands

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
	"time"

	"github.com/flow-ecosystem/umbrella-agent/internal/api"
)

// Result is the outcome of a command execution.
type Result struct {
	// Status is "success" or "failure".
	Status  string
	Output  json.RawMessage
	ErrMsg  string
}

// Execute runs the given command type with optional JSON payload.
// client is used for update_self with server-hosted releases; nil is safe for other commands.
func Execute(cmdType string, payload json.RawMessage, client *api.Client) Result {
	switch cmdType {
	case "reboot":
		return reboot()
	case "collect_diagnostics":
		return collectDiagnostics()
	case "update_self":
		return ExecuteUpdate(payload, client)
	case "decommission":
		return decommission()
	case "kill_process":
		return killProcess(payload)
	case "apply_config":
		return Result{Status: "success", Output: jsonMsg("config reloaded (noop)")}
	default:
		return Result{Status: "failure", ErrMsg: fmt.Sprintf("unknown command type: %s", cmdType)}
	}
}

func reboot() Result {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "linux":
		cmd = exec.Command("reboot")
	case "darwin":
		cmd = exec.Command("shutdown", "-r", "now")
	case "windows":
		cmd = exec.Command("shutdown", "/r", "/t", "0")
	default:
		return Result{Status: "failure", ErrMsg: "reboot: unsupported OS"}
	}

	if err := cmd.Run(); err != nil {
		return Result{Status: "failure", ErrMsg: "reboot: " + err.Error()}
	}
	return Result{Status: "success", Output: jsonMsg("reboot initiated")}
}

func collectDiagnostics() Result {
	hostname, _ := os.Hostname()

	diag := map[string]any{
		"hostname":   hostname,
		"os":         runtime.GOOS,
		"arch":       runtime.GOARCH,
		"go_version": runtime.Version(),
		"timestamp":  time.Now().UTC().Format(time.RFC3339),
	}

	if v := kernelVersion(); v != "" {
		diag["kernel_version"] = v
	}
	if m := memInfoMB(); m > 0 {
		diag["memory_total_mb"] = m
	}
	if u := uptimeSeconds(); u > 0 {
		diag["uptime_seconds"] = u
	}

	out, err := json.Marshal(diag)
	if err != nil {
		return Result{Status: "failure", ErrMsg: err.Error()}
	}
	return Result{Status: "success", Output: json.RawMessage(out)}
}

// ── OS-specific helpers ──────────────────────────────────────────────────────

func kernelVersion() string {
	if runtime.GOOS != "linux" {
		return ""
	}
	out, err := exec.Command("uname", "-r").Output()
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(out))
}

// memInfoMB returns total memory in MiB by reading /proc/meminfo on Linux.
func memInfoMB() int {
	if runtime.GOOS != "linux" {
		return 0
	}
	f, err := os.Open("/proc/meminfo")
	if err != nil {
		return 0
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		if strings.HasPrefix(line, "MemTotal:") {
			fields := strings.Fields(line)
			if len(fields) >= 2 {
				kb, err := strconv.Atoi(fields[1])
				if err == nil {
					return kb / 1024
				}
			}
			break
		}
	}
	return 0
}

// uptimeSeconds reads /proc/uptime on Linux.
func uptimeSeconds() int {
	if runtime.GOOS != "linux" {
		return 0
	}
	data, err := os.ReadFile("/proc/uptime")
	if err != nil {
		return 0
	}
	fields := strings.Fields(string(data))
	if len(fields) == 0 {
		return 0
	}
	var seconds float64
	fmt.Sscanf(fields[0], "%f", &seconds)
	return int(seconds)
}

func jsonMsg(msg string) json.RawMessage {
	b, _ := json.Marshal(map[string]string{"message": msg})
	return b
}
