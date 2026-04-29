package process

// ProcessInfo holds a snapshot of a single running process.
type ProcessInfo struct {
	Name       string  `json:"name"`
	PID        int     `json:"pid"`
	CPUPercent float64 `json:"cpu_percent"`
	MemMB      int64   `json:"mem_mb"`
}
