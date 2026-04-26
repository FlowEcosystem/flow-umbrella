//go:build windows

package enforce

import (
	"encoding/json"
	"os"
	"path/filepath"

	"golang.org/x/sys/windows/registry"
)

// chromiumPolicyKeys are HKLM registry paths for Chromium-based browser policies.
var chromiumPolicyKeys = []string{
	`SOFTWARE\Policies\Google\Chrome`,
	`SOFTWARE\Policies\Microsoft\Edge`,
	`SOFTWARE\Policies\BraveSoftware\Brave`,
	`SOFTWARE\Policies\Vivaldi`,
}

// disableBrowserDoH writes enterprise policies to all installed browsers
// forcing DNS through the system resolver (disabling built-in DoH).
func disableBrowserDoH() {
	setChromiumDoH("off")
	setFirefoxDoH(false)
}

// restoreBrowserDoH removes the DoH enforcement policies written by disableBrowserDoH.
func restoreBrowserDoH() {
	setChromiumDoH("")
	setFirefoxDoH(true)
}

// ── Chromium (Chrome / Edge / Brave / Vivaldi) ────────────────────────────────

func setChromiumDoH(mode string) {
	for _, keyPath := range chromiumPolicyKeys {
		k, _, err := registry.CreateKey(registry.LOCAL_MACHINE, keyPath, registry.SET_VALUE)
		if err != nil {
			continue
		}
		if mode == "" {
			k.DeleteValue("DnsOverHttpsMode")
		} else {
			k.SetStringValue("DnsOverHttpsMode", mode)
		}
		k.Close()
	}
}

// ── Firefox ───────────────────────────────────────────────────────────────────

// firefoxDistDirs returns candidate `distribution` directories for all Firefox
// installations found under Program Files.
func firefoxDistDirs() []string {
	var dirs []string
	for _, env := range []string{"PROGRAMFILES", "PROGRAMFILES(X86)"} {
		base := os.Getenv(env)
		if base == "" {
			continue
		}
		for _, name := range []string{"Mozilla Firefox", "Firefox"} {
			installDir := filepath.Join(base, name)
			if _, err := os.Stat(installDir); err == nil {
				dirs = append(dirs, filepath.Join(installDir, "distribution"))
			}
		}
	}
	return dirs
}

// setFirefoxDoH merges or removes the DNSOverHTTPS policy in Firefox
// policies.json, preserving any other existing policies.
func setFirefoxDoH(remove bool) {
	for _, distDir := range firefoxDistDirs() {
		policyFile := filepath.Join(distDir, "policies.json")

		// Read existing file if present.
		var root map[string]interface{}
		if data, err := os.ReadFile(policyFile); err == nil {
			json.Unmarshal(data, &root) //nolint:errcheck
		}
		if root == nil {
			root = map[string]interface{}{}
		}

		policies, _ := root["policies"].(map[string]interface{})
		if policies == nil {
			policies = map[string]interface{}{}
		}

		if remove {
			delete(policies, "DNSOverHTTPS")
		} else {
			policies["DNSOverHTTPS"] = map[string]interface{}{
				"Mode":   "off",
				"Locked": true,
			}
		}

		if len(policies) == 0 {
			os.Remove(policyFile)
			continue
		}

		root["policies"] = policies
		data, err := json.MarshalIndent(root, "", "  ")
		if err != nil {
			continue
		}
		os.MkdirAll(distDir, 0o755)
		os.WriteFile(policyFile, data, 0o644) //nolint:errcheck
	}
}
