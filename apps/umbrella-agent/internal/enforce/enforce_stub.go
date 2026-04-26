//go:build !windows

package enforce

// Non-Windows stubs — enforcement is Windows-only in phase 1.

func applyHosts(_ []string, _ string) error    { return nil }
func applyFirewall(_ []string, _ string) error { return nil }
func applyProcessBlock(_ []string) error       { return nil }
func wfpLoadState(_ string) map[string]uint64  { return nil }
