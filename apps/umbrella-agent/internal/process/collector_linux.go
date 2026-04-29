//go:build linux

package process

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

// Collect returns running processes by scanning /proc.
func Collect() ([]ProcessInfo, error) {
	entries, err := os.ReadDir("/proc")
	if err != nil {
		return nil, err
	}

	var procs []ProcessInfo
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		pid, err := strconv.Atoi(e.Name())
		if err != nil {
			continue // not a PID directory
		}
		name, memKB := readProcStatus(e.Name())
		if name == "" {
			continue
		}
		utime, stime := readProcStat(e.Name())
		cpuMS := int64((utime + stime) * 10) // jiffies @ USER_HZ=100 → ms: * 1000/100 = *10
		memMB := memKB / 1024
		if memMB == 0 && memKB > 0 {
			memMB = 1 // < 1 MB processes still show as 1
		}
		procs = append(procs, ProcessInfo{
			Name:       name,
			PID:        pid,
			CPUPercent: computeCPUPct(pid, name, cpuMS),
			MemMB:      memMB,
		})
	}
	return procs, nil
}

// readProcStat reads utime + stime from /proc/PID/stat (fields 13 and 14, 0-indexed).
func readProcStat(pid string) (utime, stime uint64) {
	data, err := os.ReadFile(filepath.Join("/proc", pid, "stat"))
	if err != nil {
		return
	}
	// stat format: pid (comm) state ppid ... utime stime ...
	// comm may contain spaces and parentheses; find last ')' to anchor field positions.
	s := string(data)
	rp := strings.LastIndex(s, ")")
	if rp < 0 {
		return
	}
	fields := strings.Fields(s[rp+1:])
	// after ')': state=0, ppid=1, pgrp=2, session=3, tty=4, tpgid=5, flags=6,
	// minflt=7, cminflt=8, majflt=9, cmajflt=10, utime=11, stime=12
	if len(fields) < 13 {
		return
	}
	utime, _ = strconv.ParseUint(fields[11], 10, 64)
	stime, _ = strconv.ParseUint(fields[12], 10, 64)
	return
}

func readProcStatus(pid string) (name string, vmRSSKB int64) {
	data, err := os.ReadFile(filepath.Join("/proc", pid, "status"))
	if err != nil {
		return "", 0
	}
	for _, line := range strings.Split(string(data), "\n") {
		if strings.HasPrefix(line, "Name:") {
			name = strings.TrimSpace(strings.TrimPrefix(line, "Name:"))
		} else if strings.HasPrefix(line, "VmRSS:") {
			fields := strings.Fields(line)
			if len(fields) >= 2 {
				vmRSSKB, _ = strconv.ParseInt(fields[1], 10, 64)
			}
		}
		if name != "" && vmRSSKB > 0 {
			break
		}
	}
	return name, vmRSSKB
}
