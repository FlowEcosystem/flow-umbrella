package commands

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

type updatePayload struct {
	URL      string `json:"url"`
	Version  string `json:"version"`
	Checksum string `json:"checksum"` // optional: "sha256:<hex>"
}

func updateSelf(raw json.RawMessage) Result {
	var p updatePayload
	if err := json.Unmarshal(raw, &p); err != nil {
		return Result{Status: "failure", ErrMsg: "invalid payload: " + err.Error()}
	}
	if p.URL == "" {
		return Result{Status: "failure", ErrMsg: "update_self: url is required in payload"}
	}

	tmpPath := os.TempDir() + string(os.PathSeparator) + "umbrella-agent-update" + exeSuffix()

	if err := downloadFile(tmpPath, p.URL); err != nil {
		return Result{Status: "failure", ErrMsg: "download: " + err.Error()}
	}

	if p.Checksum != "" {
		if err := verifySHA256(tmpPath, p.Checksum); err != nil {
			_ = os.Remove(tmpPath)
			return Result{Status: "failure", ErrMsg: "checksum: " + err.Error()}
		}
	}

	if err := applyUpdate(tmpPath); err != nil {
		_ = os.Remove(tmpPath)
		return Result{Status: "failure", ErrMsg: "apply: " + err.Error()}
	}

	msg := "update scheduled"
	if p.Version != "" {
		msg = "update to " + p.Version + " scheduled"
	}
	return Result{Status: "success", Output: jsonMsg(msg)}
}

func downloadFile(dst, url string) error {
	resp, err := http.Get(url) //nolint:gosec
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("HTTP %s", resp.Status)
	}

	f, err := os.OpenFile(dst, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o755)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = io.Copy(f, resp.Body)
	return err
}

func verifySHA256(path, expected string) error {
	expected = strings.TrimPrefix(expected, "sha256:")
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()

	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return err
	}
	got := hex.EncodeToString(h.Sum(nil))
	if got != expected {
		return fmt.Errorf("got %s, want %s", got[:16]+"...", expected[:16]+"...")
	}
	return nil
}
