package config

import (
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
)

type Config struct {
	ServerURL              string `json:"server_url"`
	EnrollmentToken        string `json:"enrollment_token"`
	StateFile              string `json:"state_file"`
	LogFile                string `json:"log_file"`
	HeartbeatIntervalSec   int    `json:"heartbeat_interval_sec"`
	CommandPollIntervalSec int    `json:"command_poll_interval_sec"`
	PolicyPollIntervalSec  int    `json:"policy_poll_interval_sec"`
	MetricsPushIntervalSec int    `json:"metrics_push_interval_sec"`
	CertRenewBeforeDays    int    `json:"cert_renew_before_days"`
	AgentVersion           string `json:"agent_version"`
	// InsecureSkipVerify skips TLS verification — dev only.
	InsecureSkipVerify bool `json:"insecure_skip_verify"`
}

func DefaultStateFile() string {
	if runtime.GOOS == "windows" {
		pd := os.Getenv("PROGRAMDATA")
		if pd == "" {
			pd = `C:\ProgramData`
		}
		return filepath.Join(pd, "UmbrellaAgent", "state.json")
	}
	return "/var/lib/umbrella-agent/state.json"
}

func DefaultLogFile() string {
	if runtime.GOOS == "windows" {
		pd := os.Getenv("PROGRAMDATA")
		if pd == "" {
			pd = `C:\ProgramData`
		}
		return filepath.Join(pd, "UmbrellaAgent", "umbrella-agent.log")
	}
	return "/var/log/umbrella-agent.log"
}

// DefaultConfigFile returns the platform config path.
// Windows: %PROGRAMDATA%\UmbrellaAgent\config.json
// Linux:   /etc/umbrella-agent/config.json
func DefaultConfigFile() string {
	if runtime.GOOS == "windows" {
		pd := os.Getenv("PROGRAMDATA")
		if pd == "" {
			pd = `C:\ProgramData`
		}
		return filepath.Join(pd, "UmbrellaAgent", "config.json")
	}
	return "/etc/umbrella-agent/config.json"
}

func defaults() Config {
	return Config{
		StateFile:              DefaultStateFile(),
		LogFile:                DefaultLogFile(),
		HeartbeatIntervalSec:   15,
		CommandPollIntervalSec: 10,
		PolicyPollIntervalSec:  60,
		MetricsPushIntervalSec: 30,
		CertRenewBeforeDays:    7,
		AgentVersion:           "0.1.0",
	}
}

// Load reads config from path (JSON). Missing file is fine — defaults apply.
// Environment variables override file values:
//
//	UMBRELLA_SERVER_URL, UMBRELLA_ENROLLMENT_TOKEN, UMBRELLA_STATE_FILE,
//	UMBRELLA_HEARTBEAT_INTERVAL, UMBRELLA_COMMAND_POLL_INTERVAL,
//	UMBRELLA_POLICY_POLL_INTERVAL, UMBRELLA_AGENT_VERSION,
//	UMBRELLA_INSECURE (1/true to skip TLS verification)
func Load(path string) (Config, error) {
	cfg := defaults()

	if path != "" {
		data, err := os.ReadFile(path)
		if err != nil && !os.IsNotExist(err) {
			return cfg, err
		}
		if err == nil {
			if err := json.Unmarshal(data, &cfg); err != nil {
				return cfg, err
			}
		}
	}

	if v := os.Getenv("UMBRELLA_SERVER_URL"); v != "" {
		cfg.ServerURL = v
	}
	if v := os.Getenv("UMBRELLA_ENROLLMENT_TOKEN"); v != "" {
		cfg.EnrollmentToken = v
	}
	if v := os.Getenv("UMBRELLA_STATE_FILE"); v != "" {
		cfg.StateFile = v
	}
	if v := os.Getenv("UMBRELLA_AGENT_VERSION"); v != "" {
		cfg.AgentVersion = v
	}
	if v := os.Getenv("UMBRELLA_HEARTBEAT_INTERVAL"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.HeartbeatIntervalSec = n
		}
	}
	if v := os.Getenv("UMBRELLA_COMMAND_POLL_INTERVAL"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.CommandPollIntervalSec = n
		}
	}
	if v := os.Getenv("UMBRELLA_POLICY_POLL_INTERVAL"); v != "" {
		if n, err := strconv.Atoi(v); err == nil {
			cfg.PolicyPollIntervalSec = n
		}
	}
	if v := os.Getenv("UMBRELLA_INSECURE"); v == "1" || v == "true" {
		cfg.InsecureSkipVerify = true
	}

	return cfg, nil
}
