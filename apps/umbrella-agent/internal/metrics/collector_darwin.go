//go:build darwin

package metrics

import (
	"syscall"
	"time"
)

func Collect() (Snapshot, error) {
	diskUsed, diskTotal, _ := diskGB("/")
	return Snapshot{
		CollectedAt: time.Now().UTC(),
		// CPU collection on macOS requires CGo or IOKit; skip for dev builds.
		CPUPercent:  0,
		RAMUsedMB:   0,
		RAMTotalMB:  0,
		DiskUsedGB:  diskUsed,
		DiskTotalGB: diskTotal,
	}, nil
}

func diskGB(path string) (float64, float64, error) {
	var stat syscall.Statfs_t
	if err := syscall.Statfs(path, &stat); err != nil {
		return 0, 0, err
	}
	total := float64(stat.Blocks) * float64(stat.Bsize)
	free := float64(stat.Bavail) * float64(stat.Bsize)
	const gb = 1 << 30
	return (total - free) / gb, total / gb, nil
}
