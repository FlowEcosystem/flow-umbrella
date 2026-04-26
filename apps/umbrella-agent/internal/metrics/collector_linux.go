//go:build linux

package metrics

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"
	"syscall"
	"time"
)

// Collect returns a resource snapshot. CPU% is measured over a ~200 ms window.
func Collect() (Snapshot, error) {
	cpu, err := cpuPercent()
	if err != nil {
		cpu = 0
	}
	used, total, err := ramMB()
	if err != nil {
		used, total = 0, 0
	}
	diskUsed, diskTotal, err := diskGB("/")
	if err != nil {
		diskUsed, diskTotal = 0, 0
	}
	return Snapshot{
		CollectedAt: time.Now().UTC(),
		CPUPercent:  cpu,
		RAMUsedMB:   used,
		RAMTotalMB:  total,
		DiskUsedGB:  diskUsed,
		DiskTotalGB: diskTotal,
	}, nil
}

// cpuPercent reads /proc/stat twice with 200 ms in between.
func cpuPercent() (float64, error) {
	t1, err := readCPUTimes()
	if err != nil {
		return 0, err
	}
	time.Sleep(200 * time.Millisecond)
	t2, err := readCPUTimes()
	if err != nil {
		return 0, err
	}

	deltaTotal := t2.total - t1.total
	deltaIdle := t2.idle - t1.idle
	if deltaTotal == 0 {
		return 0, nil
	}
	return float64(deltaTotal-deltaIdle) / float64(deltaTotal) * 100, nil
}

type cpuTimes struct{ total, idle uint64 }

func readCPUTimes() (cpuTimes, error) {
	f, err := os.Open("/proc/stat")
	if err != nil {
		return cpuTimes{}, err
	}
	defer f.Close()

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		if !strings.HasPrefix(line, "cpu ") {
			continue
		}
		fields := strings.Fields(line)[1:] // drop "cpu" label
		var vals []uint64
		for _, f := range fields {
			v, _ := strconv.ParseUint(f, 10, 64)
			vals = append(vals, v)
		}
		if len(vals) < 4 {
			return cpuTimes{}, fmt.Errorf("unexpected /proc/stat format")
		}
		idle := vals[3] // idle field
		var total uint64
		for _, v := range vals {
			total += v
		}
		return cpuTimes{total: total, idle: idle}, nil
	}
	return cpuTimes{}, fmt.Errorf("cpu line not found in /proc/stat")
}

// ramMB returns (used, total) in MiB from /proc/meminfo.
func ramMB() (int64, int64, error) {
	f, err := os.Open("/proc/meminfo")
	if err != nil {
		return 0, 0, err
	}
	defer f.Close()

	vals := map[string]int64{}
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.Fields(line)
		if len(parts) < 2 {
			continue
		}
		key := strings.TrimSuffix(parts[0], ":")
		v, _ := strconv.ParseInt(parts[1], 10, 64)
		vals[key] = v
	}
	totalKB := vals["MemTotal"]
	availKB := vals["MemAvailable"]
	if totalKB == 0 {
		return 0, 0, fmt.Errorf("MemTotal not found")
	}
	usedKB := totalKB - availKB
	return usedKB / 1024, totalKB / 1024, nil
}

// diskGB returns (used, total) in GiB for the given path.
func diskGB(path string) (float64, float64, error) {
	var stat syscall.Statfs_t
	if err := syscall.Statfs(path, &stat); err != nil {
		return 0, 0, err
	}
	total := float64(stat.Blocks) * float64(stat.Bsize)
	free := float64(stat.Bavail) * float64(stat.Bsize)
	used := total - free
	const gb = 1 << 30
	return used / gb, total / gb, nil
}
