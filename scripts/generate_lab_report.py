"""
generate_lab_report.py — Aggregate integration lab report.

Reads the telecom_nodes.csv and firewall_rules.json, validates both,
and prints a consolidated report. Designed as a post-CI artefact generator.

Usage:
  python scripts/generate_lab_report.py
  python scripts/generate_lab_report.py --nodes config/telecom_nodes.csv \
                                         --firewall config/firewall_rules.json
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class NodeReport:
    node_id:    str
    technology: str
    ip_address: str
    ssh_port:   int
    latency_ms: int
    ip_valid:   bool
    ssh_valid:  bool
    lat_ok:     bool
    status:     str


@dataclass
class FirewallFinding:
    rule_index: int
    severity:   str
    message:    str


# ---------------------------------------------------------------------------
# Node validation
# ---------------------------------------------------------------------------

def _is_valid_ipv4(ip: str) -> bool:
    import re
    pattern = r"^((25[0-5]|2[0-4]\d|1?\d{1,2})\.){3}(25[0-5]|2[0-4]\d|1?\d{1,2})$"
    return bool(re.match(pattern, ip))


def validate_nodes(csv_path: Path) -> list[NodeReport]:
    reports: list[NodeReport] = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ip       = row["ip_address"]
            port     = int(row["ssh_port"])
            latency  = int(row["expected_latency_ms"])
            ip_ok    = _is_valid_ipv4(ip)
            ssh_ok   = 0 < port <= 65535
            lat_ok   = latency <= 50
            status   = "READY" if (ip_ok and ssh_ok and lat_ok) else "CHECK_REQUIRED"
            reports.append(NodeReport(
                node_id    = row["node_id"],
                technology = row["technology"],
                ip_address = ip,
                ssh_port   = port,
                latency_ms = latency,
                ip_valid   = ip_ok,
                ssh_valid  = ssh_ok,
                lat_ok     = lat_ok,
                status     = status,
            ))
    return reports


# ---------------------------------------------------------------------------
# Firewall validation
# ---------------------------------------------------------------------------

def validate_firewall(fw_path: Path) -> list[FirewallFinding]:
    data: dict[str, Any] = json.loads(fw_path.read_text(encoding="utf-8"))
    findings: list[FirewallFinding] = []

    for i, rule in enumerate(data.get("rules", [])):
        if rule.get("source") == "PUBLIC" and rule.get("port") == 22 \
                and rule.get("action") == "ALLOW":
            findings.append(FirewallFinding(i, "HIGH",
                "Public SSH access (port 22 from PUBLIC) must be restricted."))
        if rule.get("source") == "ANY" and rule.get("destination") == "ANY" \
                and rule.get("action") == "ALLOW":
            findings.append(FirewallFinding(i, "HIGH",
                "Overly permissive Any→Any ALLOW rule."))
        if rule.get("port") == 23 and rule.get("action") == "ALLOW":
            findings.append(FirewallFinding(i, "MEDIUM",
                "Telnet (port 23) is plaintext — use SSH."))

    return findings


# ---------------------------------------------------------------------------
# Report printer
# ---------------------------------------------------------------------------

def print_report(nodes: list[NodeReport], fw: list[FirewallFinding]) -> None:
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"\n{'='*62}")
    print(f"  TELECOM INTEGRATION LAB REPORT  ·  {ts}")
    print(f"{'='*62}\n")

    # Nodes
    print(f"{'NODE':<20}{'TECH':<6}{'IP':<16}{'SSH':^5}{'LAT':^5}{'STATUS'}")
    print("-" * 62)
    for n in nodes:
        print(f"{n.node_id:<20}{n.technology:<6}{n.ip_address:<16}"
              f"{'✓' if n.ssh_valid else '✗':^5}"
              f"{'✓' if n.lat_ok else '⚠':^5}"
              f"{n.status}")

    ready = sum(1 for n in nodes if n.status == "READY")
    print(f"\nNodes: {ready}/{len(nodes)} ready for integration.\n")

    # Firewall
    print("FIREWALL POLICY")
    print("-" * 62)
    if not fw:
        print("All firewall rules passed the security baseline.\n")
    else:
        for f in fw:
            print(f"[{f.severity:^6}] Rule #{f.rule_index}: {f.message}")
        print()

    print(f"Report complete. Generated at {ts}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Telecom integration lab report generator.")
    parser.add_argument("--nodes",    default="config/telecom_nodes.csv")
    parser.add_argument("--firewall", default="config/firewall_rules.json")
    args = parser.parse_args()

    nodes = validate_nodes(Path(args.nodes))
    fw    = validate_firewall(Path(args.firewall))
    print_report(nodes, fw)


if __name__ == "__main__":
    main()
