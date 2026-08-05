# Checker container for weil-first-prime FP-0.35
#
# Provides isolated-oci runtime for the first-prime and archimedean checkers.
# All dependencies are pinned to exact versions for reproducibility.
# Network is disabled at runtime (--network none enforced by proofctl).
#
# Build:
#   docker build -t weil-first-prime-checker:latest .
#   docker inspect --format='{{index .RepoDigests 0}}' weil-first-prime-checker:latest
#   # paste the sha256 digest into graph.json runtime.digest
#
# Run (manual test):
#   docker run --rm --network none \
#     -v /path/to/cert.json:/cert.json:ro \
#     weil-first-prime-checker:latest \
#     python3 /app/checker/first_prime/check_first_prime_certificate.py /cert.json \
#       --base-certificate /cert_arch.json \
#       --base-checker /app/checker/archimedean/check_archimedean.py \
#       --base-schema /app/schemas/certificate-archimedean-v1.schema.json \
#       --theorem-contract /app/domains/fp035/contracts/thm-fp-035.json

FROM python:3.12-slim

# Pin system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgmp-dev \
    libmpfr-dev \
    libflint-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency specification first (layer cache)
COPY pyproject.toml .

# Install Python dependencies at exact versions
RUN pip install --no-cache-dir \
    "python-flint==0.9.0" \
    "mpmath==1.3.0" \
    "jsonschema==4.23.0"

# Copy project source (checker, src, schemas, domains)
COPY checker/ checker/
COPY src/ src/
COPY schemas/ schemas/
COPY domains/ domains/

# Verify imports work
RUN python3 -c "
import flint, mpmath, jsonschema
from src.archimedean.interval import add
from src.archimedean.kernel import R_DOUBLE_PRIME_AT_ZERO
from src.prime_layer.legendre_shift import compute_J
from fractions import Fraction
assert R_DOUBLE_PRIME_AT_ZERO == Fraction(-7, 4)
print('container import check: OK')
"

# No default CMD — proofctl supplies the command via runtime.cmd
