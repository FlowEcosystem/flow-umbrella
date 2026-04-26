package api

import (
	"bytes"
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

// Client talks to the Umbrella server agent API (/v1/agent/*).
type Client struct {
	baseURL    string
	agentToken string
	http       *http.Client
	insecure   bool
}

func New(baseURL string, insecureSkipVerify bool) *Client {
	transport := http.DefaultTransport.(*http.Transport).Clone()
	if insecureSkipVerify {
		transport.TLSClientConfig = &tls.Config{InsecureSkipVerify: true} //nolint:gosec
	}
	return &Client{
		baseURL:  normalizeURL(baseURL),
		insecure: insecureSkipVerify,
		http:     &http.Client{Timeout: 30 * time.Second, Transport: transport},
	}
}

// normalizeURL prepends https:// if the URL has no scheme.
// Allows users to type "api.umbrella.su" or "api.umbrella.su:8443"
// without worrying about the protocol prefix.
func normalizeURL(raw string) string {
	raw = strings.TrimSpace(raw)
	if strings.Contains(raw, "://") {
		return raw
	}
	return "https://" + raw
}

func (c *Client) SetToken(token string) {
	c.agentToken = token
}

// SetClientCert configures mTLS: the client presents certPEM/keyPEM to nginx,
// and trusts caCertPEM as the root for server-certificate verification.
// Call this after enrollment (or on startup when state already has a cert).
func (c *Client) SetClientCert(certPEM, keyPEM, caCertPEM []byte) error {
	cert, err := tls.X509KeyPair(certPEM, keyPEM)
	if err != nil {
		return fmt.Errorf("load client cert: %w", err)
	}

	// Start from the system root CAs so publicly-trusted server certs (e.g.
	// Let's Encrypt) are accepted. Then add the Branch CA so servers using a
	// private CA signed by it also work.
	pool, err := x509.SystemCertPool()
	if err != nil {
		pool = x509.NewCertPool()
	}
	pool.AppendCertsFromPEM(caCertPEM)

	tlsCfg := &tls.Config{
		Certificates:       []tls.Certificate{cert},
		RootCAs:            pool,
		InsecureSkipVerify: c.insecure, //nolint:gosec
	}

	transport := http.DefaultTransport.(*http.Transport).Clone()
	transport.TLSClientConfig = tlsCfg
	c.http.Transport = transport
	return nil
}

// ── Request helpers ──────────────────────────────────────────────────────────

func (c *Client) post(path string, body, out any) error {
	return c.do(http.MethodPost, path, body, out)
}

func (c *Client) get(path string, out any) error {
	return c.do(http.MethodGet, path, nil, out)
}

func (c *Client) do(method, path string, body, out any) error {
	var reqBody io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return err
		}
		reqBody = bytes.NewReader(b)
	}

	req, err := http.NewRequest(method, c.baseURL+path, reqBody)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")
	if c.agentToken != "" {
		req.Header.Set("Authorization", "Bearer "+c.agentToken)
	}

	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return err
	}

	if resp.StatusCode >= 400 {
		return fmt.Errorf("server returned %d: %s", resp.StatusCode, string(respBody))
	}
	if out != nil && resp.StatusCode != http.StatusNoContent {
		return json.Unmarshal(respBody, out)
	}
	return nil
}

// ── Schema types ─────────────────────────────────────────────────────────────

type EnrollRequest struct {
	EnrollmentToken string `json:"enrollment_token"`
	Hostname        string `json:"hostname"`
	OS              string `json:"os"`
	OSVersion       string `json:"os_version,omitempty"`
	AgentVersion    string `json:"agent_version,omitempty"`
	IPAddress       string `json:"ip_address,omitempty"`
	CSRPEM          string `json:"csr_pem"`
}

type EnrollResponse struct {
	AgentID                string    `json:"agent_id"`
	AgentToken             string    `json:"agent_token"`
	CertPEM                string    `json:"cert_pem"`
	CACertPEM              string    `json:"ca_cert_pem"`
	CertExpiresAt          time.Time `json:"cert_expires_at"`
	PolicyPollIntervalSec  int       `json:"policy_poll_interval_sec"`
	CommandPollIntervalSec int       `json:"command_poll_interval_sec"`
	DecommissionPubkey     string    `json:"decommission_pubkey"`
}

type HeartbeatRequest struct {
	OSVersion    string `json:"os_version,omitempty"`
	AgentVersion string `json:"agent_version,omitempty"`
	IPAddress    string `json:"ip_address,omitempty"`
}

type Command struct {
	ID        string          `json:"id"`
	Type      string          `json:"type"`
	Payload   json.RawMessage `json:"payload,omitempty"`
	ExpiresAt *time.Time      `json:"expires_at,omitempty"`
}

type CommandResultRequest struct {
	Status       string          `json:"status"`
	Result       json.RawMessage `json:"result,omitempty"`
	ErrorMessage string          `json:"error_message,omitempty"`
}

type Policy struct {
	ID      string          `json:"id"`
	Name    string          `json:"name"`
	Kind    string          `json:"kind"`
	Action  string          `json:"action"`
	Version int             `json:"version"`
	Rules   json.RawMessage `json:"rules"`
}

type RenewRequest struct {
	CSRPEM string `json:"csr_pem"`
}

type RenewResponse struct {
	CertPEM       string    `json:"cert_pem"`
	CACertPEM     string    `json:"ca_cert_pem"`
	CertExpiresAt time.Time `json:"cert_expires_at"`
}

// ── API calls ────────────────────────────────────────────────────────────────

func (c *Client) Enroll(req EnrollRequest) (EnrollResponse, error) {
	var resp EnrollResponse
	return resp, c.post("/v1/agent/enroll", req, &resp)
}

func (c *Client) Heartbeat(req HeartbeatRequest) error {
	return c.post("/v1/agent/heartbeat", req, nil)
}

func (c *Client) PollCommands() ([]Command, error) {
	var cmds []Command
	return cmds, c.get("/v1/agent/commands", &cmds)
}

func (c *Client) SubmitCommandResult(commandID string, req CommandResultRequest) error {
	return c.post("/v1/agent/commands/"+commandID+"/result", req, nil)
}

func (c *Client) GetPolicies() ([]Policy, error) {
	var policies []Policy
	return policies, c.get("/v1/agent/policies", &policies)
}

func (c *Client) RenewCert(req RenewRequest) (RenewResponse, error) {
	var resp RenewResponse
	return resp, c.post("/v1/agent/renew", req, &resp)
}
