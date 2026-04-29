package process

import (
	"sync"
	"time"
)

type cpuSample struct {
	name  string // для детектирования переиспользования PID
	cpuMS int64  // накопленное CPU-время в миллисекундах
	at    time.Time
}

var (
	sampleMu    sync.Mutex
	prevSamples = map[int]cpuSample{} // pid → последний семпл
)

// computeCPUPct возвращает средний CPU% процесса за время с прошлого семпла.
// При первом вызове (или смене имени для того же PID) возвращает 0.
func computeCPUPct(pid int, name string, cpuMS int64) float64 {
	sampleMu.Lock()
	defer sampleMu.Unlock()

	now := time.Now()
	prev, ok := prevSamples[pid]
	prevSamples[pid] = cpuSample{name: name, cpuMS: cpuMS, at: now}

	if !ok || prev.name != name {
		return 0 // первый семпл или PID переиспользован другим процессом
	}
	elapsed := now.Sub(prev.at).Seconds()
	if elapsed < 1 {
		return 0
	}
	// deltaMS / elapsed_s / 10 = deltaMS / elapsed_s / 1000 * 100
	pct := float64(cpuMS-prev.cpuMS) / elapsed / 10
	if pct < 0 {
		pct = 0 // счётчик не может уменьшаться, защита от аномалий
	}
	return pct
}
