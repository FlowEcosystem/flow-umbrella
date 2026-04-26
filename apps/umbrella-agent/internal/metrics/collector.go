// Package metrics collects host resource snapshots (CPU, RAM, disk).
package metrics

import "time"

// Snapshot is a point-in-time resource reading.
type Snapshot struct {
	CollectedAt time.Time
	CPUPercent  float64
	RAMUsedMB   int64
	RAMTotalMB  int64
	DiskUsedGB  float64
	DiskTotalGB float64
}
