//go:build !windows && !linux

package process

import "fmt"

func Collect() ([]ProcessInfo, error) {
	return nil, fmt.Errorf("process collection not supported on this platform")
}
