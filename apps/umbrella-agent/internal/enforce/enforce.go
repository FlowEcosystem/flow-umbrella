// Package enforce applies Umbrella policies to the local OS.
//
// For each policy poll cycle the agent calls Apply with the full list of active
// policies. Enforce computes a diff against previously applied rules and
// atomically updates the system: adds new rules and removes stale ones.
//
// Phase-1 Windows enforcement:
//   - traffic/domain → C:\Windows\System32\drivers\etc\hosts (0.0.0.0 <domain>)
//   - traffic/ip     → WFP userspace API (fwpuclnt.dll), outbound block
//   - DoH bypass     → Cloudflare/Google/Quad9/AdGuard IPs blocked on TCP+UDP 443
//   - process        → periodic tasklist scan + taskkill on blocked process names
package enforce

import (
	"encoding/json"
	"log/slog"
)

// Rule is a single entry from a policy's rules array.
type Rule struct {
	Type  string `json:"type"`  // "domain" | "url" | "ip" | "process"
	Value string `json:"value"`
}

// Policy mirrors the agent API response for a single policy item.
type Policy struct {
	ID     string
	Name   string
	Kind   string // "traffic" | "process"
	Action string // "block" | "allow"  (only "block" enforced in phase 1)
	Rules  []Rule
}

// ParseRules unmarshals the raw JSON rules array into []Rule.
func ParseRules(raw json.RawMessage) []Rule {
	var rules []Rule
	_ = json.Unmarshal(raw, &rules)
	return rules
}

// Apply takes the current full policy list and synchronises OS enforcement
// rules. stateFile is the agent state path used to persist WFP filter IDs.
// It is idempotent: calling it twice with the same policies is safe.
func Apply(policies []Policy, stateFile string) {
	var domains, ips, processes []string

	for _, p := range policies {
		if p.Action != "block" {
			continue
		}
		for _, r := range p.Rules {
			switch r.Type {
			case "domain":
				if r.Value != "" {
					domains = append(domains, r.Value)
				}
			case "ip":
				if r.Value != "" {
					ips = append(ips, r.Value)
				}
			case "process":
				if r.Value != "" {
					processes = append(processes, r.Value)
				}
			// "url" — not enforceable without a proxy; skip in phase 1.
			}
		}
	}

	if err := applyHosts(domains, stateFile); err != nil {
		slog.Warn("enforce: hosts update failed", "err", err)
	}
	if err := applyFirewall(ips, stateFile); err != nil {
		slog.Warn("enforce: firewall update failed", "err", err)
	}
	if err := applyProcessBlock(processes); err != nil {
		slog.Warn("enforce: process block failed", "err", err)
	}

	wfpCount := len(wfpLoadState(stateFile))
	status := EnforcementStatus{
		DNSSinkhole:    len(domains) > 0,
		BlockedDomains: len(domains),
		BlockedIPs:     len(ips),
		WFPFilters:     wfpCount,
	}
	if err := SaveEnforcementStatus(stateFile, status); err != nil {
		slog.Warn("enforce: status save failed", "err", err)
	}
}
