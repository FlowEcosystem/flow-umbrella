// Package token verifies offline decommission tokens signed by the server.
//
// The server holds an ECDSA P-256 private key. During enrollment it sends the
// matching public key (PEM), which the agent stores in state.json. To uninstall
// without server access, an admin generates a token via the management console;
// the agent verifies the signature locally using the stored public key.
//
// Token format: base64url(DER-encoded ECDSA P-256 signature over SHA-256 of
// "decommission:{agentID}:{dayStamp}", where dayStamp = UTC midnight Unix timestamp).
//
// Validity window: today and yesterday UTC (48 h) to handle day-boundary edge cases.
package token

import (
	"crypto/ecdsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"encoding/pem"
	"fmt"
	"time"
)

// Validate reports whether tok is a valid decommission token for this agent.
// pubKeyPEM is the ECDSA P-256 public key received from the server at enrollment.
func Validate(pubKeyPEM, agentID, tok string) bool {
	pub, err := parsePublicKey(pubKeyPEM)
	if err != nil {
		return false
	}
	sig, err := base64.RawURLEncoding.DecodeString(tok)
	if err != nil {
		return false
	}
	now := time.Now().UTC()
	return verifyAt(pub, agentID, sig, now) ||
		verifyAt(pub, agentID, sig, now.Add(-24*time.Hour))
}

func verifyAt(pub *ecdsa.PublicKey, agentID string, sig []byte, t time.Time) bool {
	dayStamp := t.Truncate(24 * time.Hour).Unix()
	msg := fmt.Sprintf("decommission:%s:%d", agentID, dayStamp)
	h := sha256.Sum256([]byte(msg))
	return ecdsa.VerifyASN1(pub, h[:], sig)
}

func parsePublicKey(pubKeyPEM string) (*ecdsa.PublicKey, error) {
	block, _ := pem.Decode([]byte(pubKeyPEM))
	if block == nil {
		return nil, fmt.Errorf("invalid PEM block")
	}
	pub, err := x509.ParsePKIXPublicKey(block.Bytes)
	if err != nil {
		return nil, fmt.Errorf("parse public key: %w", err)
	}
	ecPub, ok := pub.(*ecdsa.PublicKey)
	if !ok {
		return nil, fmt.Errorf("not an ECDSA key")
	}
	return ecPub, nil
}
