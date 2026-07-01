---
name: avengers-ssl
description: >
  Generate a CA certificate bundle for corporate TLS proxy environments.
  Combines system CAs with corporate root certificates so Python, curl, and
  Node.js requests all trust the proxy.
allowed-tools: Bash, Read, Write
argument-hint: "[--cert-file PATH] [--output PATH] [--dry-run]"
---

# Avengers SSL - Certificate Bundle Generator

## Overview

Corporate TLS inspection proxies intercept HTTPS and resign with a corporate
root CA. Tools that ship their own CA bundle (Python, Node.js, curl) don't
trust the proxy and fail with SSL errors.

This skill generates a merged CA bundle: system CAs + corporate root.

## Steps

### 1. Run the Script

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/avengers-ssl/scripts/create-proxy-ca-bundle.py \
  [--cert-file PATH] \
  [--output PATH] \
  [--dry-run]
```

Arguments:
- `--cert-file PATH`: Path to the corporate root cert (PEM or DER). If omitted, the script auto-detects from common locations.
- `--output PATH`: Output path for the merged bundle. Default: `~/.avengers/ca-bundle.pem`
- `--dry-run`: Print what would be done without writing files.

### 2. Interpret Output

**Exit 0 (success):** Bundle written. Report the output path and env var instructions.

**Exit 1 (error):** Report the error from stderr.

**Exit 2 (no-op):** No corporate cert found. Report that the environment may not use TLS inspection.

### 3. Report Results

After successful bundle creation:

```
CA Bundle Generated
===================
Output: ~/.avengers/ca-bundle.pem
Sources: system CAs ({N} certificates) + corporate root

To activate for all tools, add to your shell profile:
  export CURL_CA_BUNDLE=~/.avengers/ca-bundle.pem
  export REQUESTS_CA_BUNDLE=~/.avengers/ca-bundle.pem
  export NODE_EXTRA_CA_CERTS=~/.avengers/ca-bundle.pem

Note: Never prefix gh commands with these env vars.
```
