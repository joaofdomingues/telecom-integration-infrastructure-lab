# Telecom Integration Infrastructure Lab

> **Portfolio project** — C++17 tool that validates 4G/5G telecom nodes for integration readiness.  
> Parallel validation via `std::thread`, Check Point Firewall REST API client, SSH health checks.

---

## What this demonstrates

| Skill | Implementation |
|---|---|
| C++17 | `std::thread`, `std::mutex`, `std::lock_guard`, `std::unique_ptr`, `std::atomic` |
| Parallel programming | One thread per node, results aggregated with `std::mutex` — thread-safe |
| RAII | `ValidationWorker` destructor joins thread; `unique_ptr` for ownership |
| SIGTERM handling | `std::atomic<bool> g_shutdown` — async-signal-safe shutdown |
| Telecom networks | 4G + 5G NR nodes, SSH port validation, latency thresholds |
| Check Point Firewall | REST API client: login → rulebase → validate → logout (mock + real) |
| SSH protocol | `ssh_node_check.py` with Paramiko (key auth, password, dry-run) |
| Python | Type-annotated scripts, dataclasses, `unittest.mock`, pytest |
| Testing | 11 C++ tests (including 20-thread parallel test) + 12 Python tests |
| CI/CD | GitHub Actions: build → CTest → parallel run → serial run → pytest → report → SonarCloud |

---

## Build & run

```bash
# Build
mkdir build && cd build
cmake ..
cmake --build .

# Validate nodes — parallel (default)
./telecom_integration_checker config/telecom_nodes.csv

# Validate nodes — serial
./telecom_integration_checker config/telecom_nodes.csv --serial

# Cross-compile for ARM64
cmake .. -DTARGET_ARCH=aarch64 \
         -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++
```

## Test

```bash
cd build && ctest --output-on-failure   # 11 C++ tests (incl. 20-thread test)
python -m pytest tests/ -v             # 12 Python tests (Check Point + firewall)
python scripts/generate_lab_report.py  # Consolidated report
```

## Check Point Firewall demo

```bash
# Mock mode (no real appliance needed)
python scripts/checkpoint_api_client.py

# Real SMS (Management Server)
python scripts/checkpoint_api_client.py \
    --host 192.168.1.100 --user admin --password secret
```

## SSH health check

```bash
# Dry-run (local commands, no SSH needed)
python scripts/ssh_node_check.py --host 192.168.10.21 --user admin --dry-run

# Real SSH with key auth
python scripts/ssh_node_check.py --host 192.168.10.21 --user admin --key ~/.ssh/id_rsa
```

## Architecture

```
src/
  main.cpp              — Parallel worker launch, SIGTERM, --serial mode
  config_parser.cpp     — CSV → vector<TelecomNode>
  network_validator.cpp — IPv4 regex, SSH port, latency threshold (thread-safe)
  integration_report.cpp — Tabular report with detail strings
scripts/
  checkpoint_api_client.py — Check Point REST API + mock server + validation
  ssh_node_check.py        — Paramiko SSH diagnostics
  firewall_rule_validator.py — JSON firewall policy validator
  generate_lab_report.py   — Consolidated CSV + firewall report
tests/
  test_checkpoint_client.py  — 9 pytest tests
  test_firewall_validator.py — 3 pytest tests
tests_cpp/
  test_validator.cpp — 11 CTest tests incl. 20-thread parallel safety test
docs/
  vmware_lab_notes.md — VMware setup, open-vm-tools, snapshots, iptables
```

## What I would add with real infrastructure

- Replace mock Check Point server with a real SMS in a lab VLAN
- Add `libssh2` for non-blocking SSH instead of `subprocess` in Python
- Integrate with a real CMDB to pull node inventory dynamically
- Add persistent result storage (SQLite) for trend analysis across runs
