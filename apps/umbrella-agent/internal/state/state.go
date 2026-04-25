package state

import (
	"encoding/json"
	"os"
	"path/filepath"
	"time"
)

// State is persisted to disk after enrollment and updated on cert renewal.
type State struct {
	AgentID       string    `json:"agent_id"`
	AgentToken    string    `json:"agent_token"`
	CertPEM       string    `json:"cert_pem"`
	KeyPEM        string    `json:"key_pem"`
	CACertPEM     string    `json:"ca_cert_pem"`
	CertExpiresAt time.Time `json:"cert_expires_at"`
	EnrolledAt    time.Time `json:"enrolled_at"`

	// Server-negotiated poll intervals (0 = not set, use config defaults).
	CommandPollIntervalSec int `json:"command_poll_interval_sec,omitempty"`
	PolicyPollIntervalSec  int `json:"policy_poll_interval_sec,omitempty"`

	// Last successful heartbeat time — written by the agent loop, read by monitor.
	LastHeartbeatAt *time.Time `json:"last_heartbeat_at,omitempty"`
}

func (s *State) IsEnrolled() bool {
	return s.AgentID != ""
}

// Load reads state from path. Returns empty state if file does not exist.
func Load(path string) (*State, error) {
	data, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return &State{}, nil
	}
	if err != nil {
		return nil, err
	}
	var s State
	if err := json.Unmarshal(data, &s); err != nil {
		return nil, err
	}
	return &s, nil
}

// Save writes state to path atomically (write to temp, then rename).
func (s *State) Save(path string) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return err
	}
	tmp := path + ".tmp"
	if err := os.WriteFile(tmp, data, 0o600); err != nil {
		return err
	}
	return os.Rename(tmp, path)
}
