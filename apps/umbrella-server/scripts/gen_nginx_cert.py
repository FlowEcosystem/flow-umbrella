#!/usr/bin/env python3
"""Generate a TLS server certificate for nginx, signed by the Branch CA.

Usage (inside container):
    python scripts/gen_nginx_cert.py api.umbrella.su

Output:
    pki/server.crt  — certificate (give to nginx ssl_certificate)
    pki/server.key  — private key  (give to nginx ssl_certificate_key)
"""

import sys
from pathlib import Path

# Allow running from /app inside container
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from umbrella_server.pki import BranchCA

hostname = sys.argv[1] if len(sys.argv) > 1 else "localhost"

ca = BranchCA.ensure(
    cert_path=Path("pki/ca.crt"),
    key_path=Path("pki/ca.key"),
    branch_name="Umbrella",
)

ca.sign_server_cert(
    hostname=hostname,
    cert_path=Path("pki/server.crt"),
    key_path=Path("pki/server.key"),
)

print(f"\n  CA cert:      pki/ca.crt")
print(f"  Server cert:  pki/server.crt")
print(f"  Server key:   pki/server.key")
print(f"\n  Nginx config:\n")
print(f"    ssl_certificate     /path/to/pki/server.crt;")
print(f"    ssl_certificate_key /path/to/pki/server.key;")
print(f"    ssl_client_certificate /path/to/pki/ca.crt;")
print(f"    ssl_verify_client on;\n")
