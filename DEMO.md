# Demo — Telecom Integration Infrastructure Lab

## What this project demonstrates

This project simulates a telecom integration infrastructure lab for validating network nodes, SSH readiness, firewall rules and integration status.

It demonstrates:

- C++17 validation tool
- Python automation scripts
- Linux/Windows/VMware-oriented workflow
- SSH protocol awareness
- Telecom node configuration
- Firewall rule validation inspired by enterprise firewall policies
- GitHub Actions CI
- SonarQube configuration
- Optional Docker/Kubernetes files

## Tested commands

```bash
mkdir build
cd build
cmake ..
cmake --build .
./telecom_integration_checker ../config/telecom_nodes.csv
```

## Runtime output

```txt
TELECOM INTEGRATION VALIDATION REPORT
=====================================
Node            IP        SSH       Latency     Status
AVEIRO-5G-001   OK        OK        OK          READY_FOR_INTEGRATION
AVEIRO-5G-002   OK        OK        OK          READY_FOR_INTEGRATION
AVEIRO-4G-001   OK        OK        OK          READY_FOR_INTEGRATION
LAB-BROKEN-001  FAIL      FAIL      WARN        CHECK_REQUIRED
```

## Firewall validation

```txt
python scripts/firewall_rule_validator.py --rules config/firewall_rules.json
Policy: telecom_lab_policy
Firewall policy validation: OK
```

## Tests

```txt
PYTHONPATH=. pytest -q tests
...                                                                      [100%]
3 passed in 0.05s
```
