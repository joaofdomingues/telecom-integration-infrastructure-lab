# ---------------------------------------------------------------------------
# Telecom Integration Infrastructure Lab — Dockerfile
#
# Multi-stage build:
#   builder  →  compiles C++ checker + runs all C++ tests
#   runtime  →  minimal image with checker binary + Python tools
#
# Build:
#   docker build -t telecom-lab .
#
# Run — parallel validation (expect exit 2 due to broken node in CSV):
#   docker run --rm telecom-lab config/telecom_nodes.csv || true
#
# Run — serial mode:
#   docker run --rm telecom-lab config/telecom_nodes.csv --serial || true
#
# Run — Check Point API demo:
#   docker run --rm --entrypoint python3 telecom-lab \
#       scripts/checkpoint_api_client.py
#
# Run — lab report:
#   docker run --rm --entrypoint python3 telecom-lab \
#       scripts/generate_lab_report.py
# ---------------------------------------------------------------------------

# ── Stage 1: builder ───────────────────────────────────────────────────────
FROM ubuntu:22.04 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY . .

RUN cmake -B build \
        -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
        -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build --parallel "$(nproc)"

# Run C++ tests during build — fail fast if any test breaks.
RUN cd build && ctest --output-on-failure

# ── Stage 2: runtime ───────────────────────────────────────────────────────
FROM ubuntu:22.04 AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy compiled binary
COPY --from=builder /build/build/telecom_integration_checker ./telecom_integration_checker

# Copy Python scripts, config and requirements
COPY scripts/  ./scripts/
COPY tests/    ./tests/
COPY config/   ./config/
COPY docs/     ./docs/
COPY requirements.txt conftest.py ./

RUN python3 -m pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["./telecom_integration_checker"]
CMD ["config/telecom_nodes.csv"]
