# OCI Migration Guide

## Current status: `scripted` runtime

All checkers currently use `runtime.kind: "scripted"`. This is the correct
honest label for native Python checkers. `proofctl doctor` (v0.3.7+) will
show a warning:

```
⚠ runtime 'scripted' in use (fp035-cap-checker, fp035-independent-review):
  cross-machine reproducibility depends on host environment, not a pinned container
  → consider 'isolated-oci' runtime for third-party independent verification
```

This warning is informational. The checker is fully functional for
same-environment replay. For third-party independent verification, migrate
to `isolated-oci`.

## What isolated-oci provides

- **Pinned image digest**: `runtime.digest: "sha256:<hex>"` in graph.json
  binds the exact container image used for every attestation
- **Network isolation**: `--network none` enforced by proofctl OCI runner
- **Read-only rootfs**: host filesystem not reachable from checker
- **Cross-machine reproducibility**: any machine that can pull the image
  can independently verify any attestation

## Migration steps

### 1. Build the container

```bash
docker build -t weil-first-prime-checker:latest .
```

### 2. Get the image digest

```bash
docker inspect --format='{{index .RepoDigests 0}}' weil-first-prime-checker:latest
# or after push:
# sha256:abc123...
```

### 3. Push to a registry

```bash
docker tag weil-first-prime-checker:latest ghcr.io/telleroutlook/weil-first-prime-checker:latest
docker push ghcr.io/telleroutlook/weil-first-prime-checker:latest
```

### 4. Update graph.json checkers

Replace in `.proofctl/graph.json`:

```json
"runtime": {
  "kind": "isolated-oci",
  "cmd": ["python3", "/app/checker/first_prime/check_first_prime_certificate.py"],
  "digest": "sha256:<image-digest-from-step-2>"
}
```

### 5. Re-pin the checker

```bash
proofctl pin checker \
  --cmd "python3 /app/checker/first_prime/check_first_prime_certificate.py" \
  --lock environment.lock \
  --schema schemas/certificate-first-prime-v1.schema.json
```

### 6. Rebuild attestations

```bash
proofctl cache invalidate --all
proofctl check --all
```

## When to migrate

**Before** submitting for publication or external review, migrate to
`isolated-oci`. The `scripted` runtime is sufficient for:
- Development and internal verification
- Same-machine replay during O1-B/O2 closure
- proofctl release gate evaluation (the gate does not require OCI)

**After** O1-B and O2 close and a PASS candidate exists, migrate to
`isolated-oci` so any third party can independently verify the certificate
without trusting the author's Python environment.

## Dockerfile notes

The `Dockerfile` at the repo root pins:
- `python-flint==0.9.0`
- `mpmath==1.3.0`
- `jsonschema==4.23.0`

These match `environment.lock`. If dependency versions change, update both
files together and re-pin the checker.
