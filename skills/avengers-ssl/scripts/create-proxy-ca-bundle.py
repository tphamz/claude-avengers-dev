#!/usr/bin/env python3
"""
create-proxy-ca-bundle.py - Generate a merged CA bundle for TLS proxy environments.

Combines system CA certificates with a corporate root certificate so tools that
ship their own CA bundle (Python requests, Node.js, curl) trust the proxy.

Exit codes:
  0 = bundle written successfully
  1 = error
  2 = no-op (no corporate cert found, nothing to do)
"""
from __future__ import annotations

import argparse
import shutil
import ssl
import subprocess
import sys
import tempfile
from pathlib import Path

COMMON_CERT_LOCATIONS = [
    # macOS
    Path("/Library/Application Support/Netskope/STAgent/data/nscacert.pem"),
    Path("/Library/Application Support/Zscaler/RootCertificate/ZscalerRootCertificate-2048-SHA256.crt"),
    Path("/usr/local/share/ca-certificates/corporate-root.crt"),
    # Linux
    Path("/etc/ssl/certs/corporate-root.pem"),
    Path("/etc/pki/ca-trust/source/anchors/corporate-root.pem"),
]


def find_corporate_cert() -> Path | None:
    """Auto-detect corporate root cert from common locations."""
    for path in COMMON_CERT_LOCATIONS:
        if path.exists():
            return path
    return None


def get_system_ca_bundle() -> bytes:
    """Extract system CA bundle as PEM bytes."""
    # Try certifi first
    try:
        import certifi
        return Path(certifi.where()).read_bytes()
    except ImportError:
        pass

    # Try ssl module's default CA path
    ca_file = ssl.get_default_verify_paths().cafile
    if ca_file and Path(ca_file).exists():
        return Path(ca_file).read_bytes()

    # Try common system locations
    system_locations = [
        Path("/etc/ssl/certs/ca-certificates.crt"),  # Debian/Ubuntu
        Path("/etc/pki/tls/certs/ca-bundle.crt"),    # RHEL/CentOS
        Path("/etc/ssl/cert.pem"),                    # macOS/OpenBSD
        Path("/usr/local/etc/openssl/cert.pem"),      # Homebrew macOS
    ]
    for loc in system_locations:
        if loc.exists():
            return loc.read_bytes()

    print("ERROR: Could not locate system CA bundle", file=sys.stderr)
    sys.exit(1)


def convert_to_pem(cert_path: Path) -> bytes:
    """Convert cert to PEM format if needed (handles DER input)."""
    data = cert_path.read_bytes()
    # DER certs start with a specific byte sequence
    if data[:2] == b'\x30\x82' or data[:2] == b'\x30\x81':
        # Likely DER, convert to PEM
        try:
            result = subprocess.run(
                ["openssl", "x509", "-inform", "DER", "-outform", "PEM"],
                input=data, capture_output=True
            )
            if result.returncode == 0:
                return result.stdout
            print(f"ERROR: Failed to convert DER cert: {result.stderr.decode()}", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError:
            print("ERROR: openssl not found (required to convert DER certificates)", file=sys.stderr)
            sys.exit(1)
    return data  # Already PEM


def main():
    parser = argparse.ArgumentParser(
        description="Generate a merged CA bundle for TLS proxy environments"
    )
    parser.add_argument(
        "--cert-file",
        type=Path,
        help="Path to corporate root certificate (PEM or DER). Auto-detects if omitted."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / ".avengers" / "ca-bundle.pem",
        help="Output path for merged bundle (default: ~/.avengers/ca-bundle.pem)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing files"
    )
    args = parser.parse_args()

    # Locate corporate cert
    corp_cert_path = args.cert_file
    if corp_cert_path is None:
        corp_cert_path = find_corporate_cert()

    if corp_cert_path is None:
        print(
            "No corporate root certificate found. "
            "Environment may not use TLS inspection.",
            file=sys.stderr
        )
        sys.exit(2)

    if not corp_cert_path.exists():
        print(f"ERROR: Certificate file not found: {corp_cert_path}", file=sys.stderr)
        sys.exit(1)

    # Get system CAs
    system_cas = get_system_ca_bundle()

    # Convert corp cert to PEM
    corp_cert_pem = convert_to_pem(corp_cert_path)

    # Build merged bundle
    merged = system_cas
    if not merged.endswith(b'\n'):
        merged += b'\n'
    merged += b'\n# Corporate Root CA\n'
    merged += corp_cert_pem

    if args.dry_run:
        print(f"Would write merged bundle to: {args.output}")
        print(f"System CAs: {len(system_cas)} bytes")
        print(f"Corporate cert: {corp_cert_path}")
        print(f"Total bundle: {len(merged)} bytes")
        sys.exit(0)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Backup existing bundle
    if args.output.exists():
        backup = args.output.with_suffix(".pem.bak")
        shutil.copy2(args.output, backup)

    args.output.write_bytes(merged)
    print(f"Bundle written: {args.output}")
    print(f"Sources: system CAs + {corp_cert_path.name}")
    sys.exit(0)


if __name__ == "__main__":
    main()
