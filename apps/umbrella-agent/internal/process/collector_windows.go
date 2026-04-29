//go:build windows

package process

import (
	"encoding/json"
	"os/exec"
)

type psProc struct {
	Name       string   `json:"Name"`
	Id         int      `json:"Id"`
	CPU        *float64 `json:"CPU"`        // total CPU seconds; null for system procs
	WorkingSet *int64   `json:"WorkingSet"` // bytes; null for some system procs
}

// Collect returns the list of running processes via PowerShell Get-Process.
// PowerShell outputs UTF-8 JSON, so Cyrillic process names are handled correctly.
func Collect() ([]ProcessInfo, error) {
	const script = `Get-Process | Select-Object Name,Id,CPU,WorkingSet | ConvertTo-Json -Compress -Depth 1`
	out, err := exec.Command("powershell", "-NoProfile", "-NonInteractive", "-Command", script).Output()
	if err != nil {
		return nil, err
	}

	// PowerShell emits a bare object (not array) when only one process exists.
	var raw []psProc
	if err := json.Unmarshal(out, &raw); err != nil {
		var single psProc
		if err2 := json.Unmarshal(out, &single); err2 != nil {
			return nil, err
		}
		raw = append(raw, single)
	}

	procs := make([]ProcessInfo, 0, len(raw))
	for _, p := range raw {
		var cpuMS int64
		if p.CPU != nil {
			cpuMS = int64(*p.CPU * 1000)
		}
		var memMB int64
		if p.WorkingSet != nil {
			memMB = *p.WorkingSet / 1024 / 1024
			if memMB == 0 && *p.WorkingSet > 0 {
				memMB = 1
			}
		}
		procs = append(procs, ProcessInfo{
			Name:       p.Name,
			PID:        p.Id,
			CPUPercent: computeCPUPct(p.Id, p.Name, cpuMS),
			MemMB:      memMB,
		})
	}
	return procs, nil
}
