package agent

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"net"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"time"

	"github.com/flow-ecosystem/umbrella-agent/internal/api"
	"github.com/flow-ecosystem/umbrella-agent/internal/commands"
	"github.com/flow-ecosystem/umbrella-agent/internal/config"
	"github.com/flow-ecosystem/umbrella-agent/internal/enforce"
	"github.com/flow-ecosystem/umbrella-agent/internal/pki"
	"github.com/flow-ecosystem/umbrella-agent/internal/state"
)

// Agent is the main runtime: handles enrollment, heartbeat, command polling,
// policy polling and certificate renewal.
type Agent struct {
	cfg    config.Config
	state  *state.State
	client *api.Client
	log    *slog.Logger
}

func New(cfg config.Config, s *state.State) *Agent {
	return &Agent{
		cfg:    cfg,
		state:  s,
		client: api.New(cfg.ServerURL, cfg.InsecureSkipVerify),
		log:    slog.Default(),
	}
}

// Enroll performs first-time enrollment: generates a key pair, sends CSR,
// persists received credentials to state file.
func (a *Agent) Enroll() error {
	if a.cfg.EnrollmentToken == "" {
		return fmt.Errorf("enrollment_token is required for enrollment")
	}

	a.log.Info("generating RSA key pair")
	key, err := pki.GenerateKey()
	if err != nil {
		return fmt.Errorf("generate key: %w", err)
	}

	hostname, err := os.Hostname()
	if err != nil {
		return fmt.Errorf("get hostname: %w", err)
	}

	csrPEM, err := pki.GenerateCSR(key, hostname)
	if err != nil {
		return fmt.Errorf("generate CSR: %w", err)
	}

	a.log.Info("enrolling with server", "hostname", hostname, "server", a.cfg.ServerURL)

	resp, err := a.client.Enroll(api.EnrollRequest{
		EnrollmentToken: a.cfg.EnrollmentToken,
		Hostname:        hostname,
		OS:              goOSToAgentOS(),
		OSVersion:       osVersion(),
		AgentVersion:    a.cfg.AgentVersion,
		IPAddress:       primaryIP(),
		CSRPEM:          csrPEM,
	})
	if err != nil {
		return fmt.Errorf("enroll: %w", err)
	}

	a.state.AgentID = resp.AgentID
	a.state.AgentToken = resp.AgentToken
	a.state.CertPEM = resp.CertPEM
	a.state.KeyPEM = pki.EncodeKeyPEM(key)
	a.state.CACertPEM = resp.CACertPEM
	a.state.CertExpiresAt = resp.CertExpiresAt
	a.state.EnrolledAt = time.Now().UTC()
	if resp.DecommissionPubkey != "" {
		a.state.DecommissionPublicKey = resp.DecommissionPubkey
	}

	if err := a.state.Save(a.cfg.StateFile); err != nil {
		return fmt.Errorf("save state: %w", err)
	}

	// Use server-suggested poll intervals if provided, and persist them.
	if resp.CommandPollIntervalSec > 0 {
		a.cfg.CommandPollIntervalSec = resp.CommandPollIntervalSec
		a.state.CommandPollIntervalSec = resp.CommandPollIntervalSec
	}
	if resp.PolicyPollIntervalSec > 0 {
		a.cfg.PolicyPollIntervalSec = resp.PolicyPollIntervalSec
		a.state.PolicyPollIntervalSec = resp.PolicyPollIntervalSec
	}

	a.client.SetToken(resp.AgentToken)

	if err := a.client.SetClientCert(
		[]byte(resp.CertPEM),
		[]byte(a.state.KeyPEM),
		[]byte(resp.CACertPEM),
	); err != nil {
		return fmt.Errorf("configure mTLS: %w", err)
	}

	a.log.Info("enrollment successful", "agent_id", resp.AgentID, "cert_expires", resp.CertExpiresAt.Format(time.RFC3339))
	return nil
}

// Run starts all background loops. Blocks until ctx is cancelled (via os.Signal
// handling in main). Uses a simple done channel for shutdown.
func (a *Agent) Run(done <-chan struct{}) {
	a.client.SetToken(a.state.AgentToken)

	if a.state.CertPEM != "" && a.state.KeyPEM != "" && a.state.CACertPEM != "" {
		if err := a.client.SetClientCert(
			[]byte(a.state.CertPEM),
			[]byte(a.state.KeyPEM),
			[]byte(a.state.CACertPEM),
		); err != nil {
			a.log.Warn("failed to configure mTLS, falling back to Bearer-only", "err", err)
		} else {
			a.log.Info("mTLS configured", "cert_expires", a.state.CertExpiresAt.Format(time.RFC3339))
		}
	}

	// Restore server-negotiated intervals persisted from last enrollment.
	if a.state.CommandPollIntervalSec > 0 {
		a.cfg.CommandPollIntervalSec = a.state.CommandPollIntervalSec
	}
	if a.state.PolicyPollIntervalSec > 0 {
		a.cfg.PolicyPollIntervalSec = a.state.PolicyPollIntervalSec
	}

	heartbeat := time.Duration(a.cfg.HeartbeatIntervalSec) * time.Second
	cmdPoll := time.Duration(a.cfg.CommandPollIntervalSec) * time.Second
	policyPoll := time.Duration(a.cfg.PolicyPollIntervalSec) * time.Second
	certCheck := 6 * time.Hour

	a.log.Info("agent running",
		"agent_id", a.state.AgentID,
		"heartbeat_interval", heartbeat,
		"command_poll_interval", cmdPoll,
	)

	// Initial beats before tickers fire.
	a.doHeartbeat()
	a.doCommandPoll()
	a.doPolicyPoll()

	heartbeatTick := time.NewTicker(heartbeat)
	cmdTick := time.NewTicker(cmdPoll)
	policyTick := time.NewTicker(policyPoll)
	certTick := time.NewTicker(certCheck)
	defer heartbeatTick.Stop()
	defer cmdTick.Stop()
	defer policyTick.Stop()
	defer certTick.Stop()

	for {
		select {
		case <-done:
			a.log.Info("agent shutting down")
			enforce.Apply(nil, a.cfg.StateFile) // restore DNS, stop sinkhole
			return
		case <-heartbeatTick.C:
			a.doHeartbeat()
		case <-cmdTick.C:
			a.doCommandPoll()
		case <-policyTick.C:
			a.doPolicyPoll()
		case <-certTick.C:
			a.doCertCheck()
		}
	}
}

// ── Heartbeat ────────────────────────────────────────────────────────────────

func (a *Agent) doHeartbeat() {
	err := a.client.Heartbeat(api.HeartbeatRequest{
		OSVersion:    osVersion(),
		AgentVersion: a.cfg.AgentVersion,
		IPAddress:    primaryIP(),
	})
	if err != nil {
		a.log.Warn("heartbeat failed", "err", err)
		return
	}
	now := time.Now().UTC()
	a.state.LastHeartbeatAt = &now
	if saveErr := a.state.Save(a.cfg.StateFile); saveErr != nil {
		a.log.Warn("failed to save heartbeat time", "err", saveErr)
	}
	a.log.Debug("heartbeat ok")
}

// ── Command polling ──────────────────────────────────────────────────────────

func (a *Agent) doCommandPoll() {
	cmds, err := a.client.PollCommands()
	if err != nil {
		a.log.Warn("command poll failed", "err", err)
		return
	}
	if len(cmds) == 0 {
		return
	}
	a.log.Info("received commands", "count", len(cmds))
	for _, cmd := range cmds {
		a.executeCommand(cmd)
	}
}

func (a *Agent) executeCommand(cmd api.Command) {
	// Skip expired commands.
	if cmd.ExpiresAt != nil && cmd.ExpiresAt.Before(time.Now()) {
		a.log.Warn("skipping expired command", "id", cmd.ID, "type", cmd.Type)
		_ = a.client.SubmitCommandResult(cmd.ID, api.CommandResultRequest{
			Status:       "timeout",
			ErrorMessage: "command expired before execution",
		})
		return
	}

	a.log.Info("executing command", "id", cmd.ID, "type", cmd.Type)

	// sync_policies: report success, then immediately repoll so the admin
	// sees the new policy applied in seconds rather than waiting up to 60s.
	if cmd.Type == "sync_policies" {
		_ = a.client.SubmitCommandResult(cmd.ID, api.CommandResultRequest{
			Status: "success",
			Result: json.RawMessage(`{"message":"policy sync triggered"}`),
		})
		a.doPolicyPoll()
		return
	}

	if cmd.Type == "decommission" {
		a.log.Info("decommission command received, cleaning up")
		_ = a.client.SubmitCommandResult(cmd.ID, api.CommandResultRequest{
			Status: "success",
			Result: json.RawMessage(`{"message":"agent decommissioning"}`),
		})
		enforce.Apply(nil, a.cfg.StateFile) // restore DNS, stop sinkhole
		commands.Execute("decommission", nil) // launch cleanup script
		os.Exit(0)
		return
	}

	// Reboot kills the process before we can report back, so report first.
	if cmd.Type == "reboot" {
		_ = a.client.SubmitCommandResult(cmd.ID, api.CommandResultRequest{
			Status: "success",
			Result: json.RawMessage(`{"message":"reboot initiated"}`),
		})
		commands.Execute(cmd.Type, cmd.Payload)
		return
	}

	result := commands.Execute(cmd.Type, cmd.Payload)

	req := api.CommandResultRequest{
		Status:       result.Status,
		Result:       result.Output,
		ErrorMessage: result.ErrMsg,
	}
	if err := a.client.SubmitCommandResult(cmd.ID, req); err != nil {
		a.log.Warn("failed to submit command result", "id", cmd.ID, "err", err)
		return
	}
	a.log.Info("command result submitted", "id", cmd.ID, "status", result.Status)
}

// ── Policy polling ───────────────────────────────────────────────────────────

func (a *Agent) doPolicyPoll() {
	apiPolicies, err := a.client.GetPolicies()
	if err != nil {
		a.log.Warn("policy poll failed", "err", err)
		return
	}
	a.log.Debug("policies received", "count", len(apiPolicies))

	var policies []enforce.Policy
	for _, p := range apiPolicies {
		policies = append(policies, enforce.Policy{
			ID:     p.ID,
			Name:   p.Name,
			Kind:   p.Kind,
			Action: p.Action,
			Rules:  enforce.ParseRules(p.Rules),
		})
	}
	enforce.Apply(policies, a.cfg.StateFile)

	if err := enforce.SaveState(a.cfg.StateFile, policies); err != nil {
		a.log.Warn("policy state save failed", "path", enforce.PolicyStatePath(a.cfg.StateFile), "err", err)
	} else {
		a.log.Debug("policy state saved", "path", enforce.PolicyStatePath(a.cfg.StateFile), "count", len(policies))
	}
}

// ── Certificate renewal ──────────────────────────────────────────────────────

func (a *Agent) doCertCheck() {
	renewBefore := time.Duration(a.cfg.CertRenewBeforeDays) * 24 * time.Hour
	if time.Until(a.state.CertExpiresAt) > renewBefore {
		return
	}

	a.log.Info("certificate nearing expiry — renewing",
		"expires_at", a.state.CertExpiresAt.Format(time.RFC3339),
	)

	key, err := pki.DecodeKeyPEM(a.state.KeyPEM)
	if err != nil {
		a.log.Error("failed to decode stored key for renewal", "err", err)
		return
	}

	csrPEM, err := pki.GenerateCSR(key, a.state.AgentID)
	if err != nil {
		a.log.Error("failed to generate CSR for renewal", "err", err)
		return
	}

	resp, err := a.client.RenewCert(api.RenewRequest{CSRPEM: csrPEM})
	if err != nil {
		a.log.Error("cert renewal request failed", "err", err)
		return
	}

	a.state.CertPEM = resp.CertPEM
	a.state.CACertPEM = resp.CACertPEM
	a.state.CertExpiresAt = resp.CertExpiresAt

	if err := a.state.Save(a.cfg.StateFile); err != nil {
		a.log.Error("failed to save state after cert renewal", "err", err)
		return
	}

	if err := a.client.SetClientCert(
		[]byte(resp.CertPEM),
		[]byte(a.state.KeyPEM),
		[]byte(resp.CACertPEM),
	); err != nil {
		a.log.Error("failed to reload mTLS cert after renewal", "err", err)
		return
	}

	a.log.Info("certificate renewed", "new_expires_at", resp.CertExpiresAt.Format(time.RFC3339))
}

// ── OS helpers ───────────────────────────────────────────────────────────────

func goOSToAgentOS() string {
	switch runtime.GOOS {
	case "darwin":
		return "macos"
	case "windows":
		return "windows"
	default:
		return "linux"
	}
}

func osVersion() string {
	switch runtime.GOOS {
	case "linux":
		v, _ := readOSRelease()
		return v
	case "darwin":
		out, _ := execOutput("sw_vers", "-productVersion")
		return strings.TrimSpace(out)
	case "windows":
		out, _ := execOutput("cmd", "/C", "ver")
		return strings.TrimSpace(out)
	default:
		return ""
	}
}

func readOSRelease() (string, error) {
	data, err := os.ReadFile("/etc/os-release")
	if err != nil {
		return "", err
	}
	for _, line := range strings.Split(string(data), "\n") {
		if strings.HasPrefix(line, "PRETTY_NAME=") {
			v := strings.TrimPrefix(line, "PRETTY_NAME=")
			return strings.Trim(v, `"`), nil
		}
	}
	return "", nil
}

// primaryIP returns the first non-loopback IPv4 address.
func primaryIP() string {
	addrs, err := net.InterfaceAddrs()
	if err != nil {
		return ""
	}
	for _, addr := range addrs {
		var ip net.IP
		switch v := addr.(type) {
		case *net.IPNet:
			ip = v.IP
		case *net.IPAddr:
			ip = v.IP
		}
		if ip == nil || ip.IsLoopback() {
			continue
		}
		if ip4 := ip.To4(); ip4 != nil {
			return ip4.String()
		}
	}
	return ""
}

func execOutput(name string, args ...string) (string, error) {
	out, err := exec.Command(name, args...).Output()
	return string(out), err
}
