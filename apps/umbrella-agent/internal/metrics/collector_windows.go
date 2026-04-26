//go:build windows

package metrics

import (
	"fmt"
	"syscall"
	"time"
	"unsafe"
)

var (
	kernel32             = syscall.NewLazyDLL("kernel32.dll")
	procGetSystemTimes   = kernel32.NewProc("GetSystemTimes")
	procGlobalMemoryStatusEx = kernel32.NewProc("GlobalMemoryStatusEx")
	procGetDiskFreeSpaceExW  = kernel32.NewProc("GetDiskFreeSpaceExW")
)

type fileTime struct{ LowDateTime, HighDateTime uint32 }

func (f fileTime) toUint64() uint64 {
	return uint64(f.HighDateTime)<<32 | uint64(f.LowDateTime)
}

type memoryStatusEx struct {
	dwLength                uint32
	dwMemoryLoad            uint32
	ullTotalPhys            uint64
	ullAvailPhys            uint64
	ullTotalPageFile        uint64
	ullAvailPageFile        uint64
	ullTotalVirtual         uint64
	ullAvailVirtual         uint64
	ullAvailExtendedVirtual uint64
}

func Collect() (Snapshot, error) {
	cpu, err := cpuPercent()
	if err != nil {
		cpu = 0
	}
	used, total, err := ramMB()
	if err != nil {
		used, total = 0, 0
	}
	diskUsed, diskTotal, err := diskGB(`C:\`)
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

func getSystemTimes() (idle, kernel, user fileTime, err error) {
	r, _, e := procGetSystemTimes.Call(
		uintptr(unsafe.Pointer(&idle)),
		uintptr(unsafe.Pointer(&kernel)),
		uintptr(unsafe.Pointer(&user)),
	)
	if r == 0 {
		err = e
	}
	return
}

func cpuPercent() (float64, error) {
	i1, k1, u1, err := getSystemTimes()
	if err != nil {
		return 0, fmt.Errorf("GetSystemTimes: %w", err)
	}
	time.Sleep(200 * time.Millisecond)
	i2, k2, u2, err := getSystemTimes()
	if err != nil {
		return 0, fmt.Errorf("GetSystemTimes: %w", err)
	}

	dIdle := i2.toUint64() - i1.toUint64()
	dKernel := k2.toUint64() - k1.toUint64() // includes idle
	dUser := u2.toUint64() - u1.toUint64()
	total := dKernel + dUser
	if total == 0 {
		return 0, nil
	}
	// kernel time includes idle time on Windows.
	busy := total - dIdle
	return float64(busy) / float64(total) * 100, nil
}

func ramMB() (int64, int64, error) {
	var ms memoryStatusEx
	ms.dwLength = uint32(unsafe.Sizeof(ms))
	r, _, e := procGlobalMemoryStatusEx.Call(uintptr(unsafe.Pointer(&ms)))
	if r == 0 {
		return 0, 0, fmt.Errorf("GlobalMemoryStatusEx: %w", e)
	}
	const mb = 1 << 20
	total := int64(ms.ullTotalPhys) / mb
	avail := int64(ms.ullAvailPhys) / mb
	return total - avail, total, nil
}

func diskGB(path string) (float64, float64, error) {
	pathPtr, err := syscall.UTF16PtrFromString(path)
	if err != nil {
		return 0, 0, err
	}
	var freeBytesAvail, totalBytes, totalFreeBytes uint64
	r, _, e := procGetDiskFreeSpaceExW.Call(
		uintptr(unsafe.Pointer(pathPtr)),
		uintptr(unsafe.Pointer(&freeBytesAvail)),
		uintptr(unsafe.Pointer(&totalBytes)),
		uintptr(unsafe.Pointer(&totalFreeBytes)),
	)
	if r == 0 {
		return 0, 0, fmt.Errorf("GetDiskFreeSpaceEx: %w", e)
	}
	const gb = 1 << 30
	used := float64(totalBytes-totalFreeBytes) / gb
	total := float64(totalBytes) / gb
	return used, total, nil
}
