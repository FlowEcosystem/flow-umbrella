package enforce

import (
	"encoding/json"
	"os"
	"path/filepath"
	"time"
)

// PolicyState is persisted to disk after each successful Apply() cycle.
// The TUI reads it to display current policy status without an API call.
type PolicyState struct {
	AppliedAt time.Time    `json:"applied_at"`
	Policies  []PolicyInfo `json:"policies"`
}

type PolicyInfo struct {
	ID        string `json:"id"`
	Name      string `json:"name"`
	Kind      string `json:"kind"`
	Action    string `json:"action"`
	Domains   int    `json:"domains,omitempty"`
	IPs       int    `json:"ips,omitempty"`
	Processes int    `json:"processes,omitempty"`
	URLs      int    `json:"urls,omitempty"`
}

// SaveState writes the current policy snapshot next to stateFile.
func SaveState(stateFile string, policies []Policy) error {
	ps := PolicyState{
		AppliedAt: time.Now().UTC(),
		Policies:  make([]PolicyInfo, 0, len(policies)),
	}
	for _, p := range policies {
		info := PolicyInfo{
			ID:     p.ID,
			Name:   p.Name,
			Kind:   p.Kind,
			Action: p.Action,
		}
		for _, r := range p.Rules {
			switch r.Type {
			case "domain":
				info.Domains++
			case "ip":
				info.IPs++
			case "process":
				info.Processes++
			case "url":
				info.URLs++
			}
		}
		ps.Policies = append(ps.Policies, info)
	}

	path := PolicyStatePath(stateFile)
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(ps, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}

// LoadState reads the policy snapshot from disk.
// Returns (nil, nil) if the file doesn't exist yet,
// or (nil, err) on a read/parse error.
func LoadState(stateFile string) (*PolicyState, error) {
	data, err := os.ReadFile(PolicyStatePath(stateFile))
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var ps PolicyState
	if err := json.Unmarshal(data, &ps); err != nil {
		return nil, err
	}
	return &ps, nil
}

// PolicyStatePath returns the path of the policies snapshot file.
func PolicyStatePath(stateFile string) string {
	return filepath.Join(filepath.Dir(stateFile), "policies.json")
}

// ── Enforcement status ────────────────────────────────────────────────────────

// EnforcementStatus reflects the active enforcement state written after each
// Apply() cycle. Read by the monitor/TUI to show what's actually running.
type EnforcementStatus struct {
	UpdatedAt      time.Time `json:"updated_at"`
	DNSSinkhole    bool      `json:"dns_sinkhole_active"`
	BlockedDomains int       `json:"blocked_domains"`
	BlockedIPs     int       `json:"blocked_ips"`
	WFPFilters     int       `json:"wfp_filters"`
}

func EnforcementStatusPath(stateFile string) string {
	return filepath.Join(filepath.Dir(stateFile), "enforcement-status.json")
}

func SaveEnforcementStatus(stateFile string, s EnforcementStatus) error {
	s.UpdatedAt = time.Now().UTC()
	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(EnforcementStatusPath(stateFile), data, 0o644)
}

func LoadEnforcementStatus(stateFile string) (*EnforcementStatus, error) {
	data, err := os.ReadFile(EnforcementStatusPath(stateFile))
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var s EnforcementStatus
	if err := json.Unmarshal(data, &s); err != nil {
		return nil, err
	}
	return &s, nil
}
