"""
ssh_node_check.py — SSH availability and health checker for telecom nodes.

Supports two modes:
  --dry-run   Run diagnostic commands locally (safe for CI and demos).
  (default)   Connect to the target node via Paramiko and run checks remotely.

Usage examples:
  python scripts/ssh_node_check.py --host 192.168.10.21 --user admin --dry-run
  python scripts/ssh_node_check.py --host 192.168.10.21 --user admin --key ~/.ssh/id_rsa
  python scripts/ssh_node_check.py --host 192.168.10.21 --user admin --password secret
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class NodeCheckResult:
    label:   str
    command: str
    output:  str
    success: bool


# ---------------------------------------------------------------------------
# Diagnostic commands
# ---------------------------------------------------------------------------

DIAG_COMMANDS: list[tuple[str, str]] = [
    ("hostname",  "hostname"),
    ("uptime",    "uptime"),
    ("disk",      "df -h / | tail -1"),
    ("network",   "ip addr show | head -20"),
]


# ---------------------------------------------------------------------------
# Local execution (dry-run / localhost)
# ---------------------------------------------------------------------------

def run_local(label: str, command: str) -> NodeCheckResult:
    try:
        proc = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=10
        )
        return NodeCheckResult(
            label=label,
            command=command,
            output=proc.stdout.strip() or proc.stderr.strip() or "(no output)",
            success=(proc.returncode == 0),
        )
    except Exception as exc:
        return NodeCheckResult(label=label, command=command,
                               output=str(exc), success=False)


# ---------------------------------------------------------------------------
# Remote execution via Paramiko
# ---------------------------------------------------------------------------

def run_remote(host: str, user: str, key_path: str | None,
               password: str | None, label: str, command: str) -> NodeCheckResult:
    """Execute *command* on *host* via Paramiko SSH."""
    try:
        import paramiko
    except ImportError:
        return NodeCheckResult(
            label=label, command=command,
            output="paramiko not installed — run: pip install paramiko",
            success=False,
        )

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        kwargs: dict = dict(hostname=host, username=user, timeout=10)
        if key_path:
            kwargs["key_filename"] = key_path
        elif password:
            kwargs["password"] = password
        else:
            kwargs["look_for_keys"] = True

        client.connect(**kwargs)
        _, stdout, stderr = client.exec_command(command, timeout=10)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        rc  = stdout.channel.recv_exit_status()

        return NodeCheckResult(
            label=label, command=command,
            output=out or err or "(no output)",
            success=(rc == 0),
        )
    except Exception as exc:
        return NodeCheckResult(label=label, command=command,
                               output=str(exc), success=False)
    finally:
        client.close()


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(results: list[NodeCheckResult], target: str) -> None:
    print(f"\n{'='*60}")
    print(f"  Telecom Node SSH Check — {target}")
    print(f"{'='*60}\n")
    for r in results:
        status = "OK" if r.success else "FAIL"
        print(f"[{r.label.upper():<12}] [{status}]")
        for line in r.output.splitlines():
            print(f"    {line}")
        print()

    failed = [r for r in results if not r.success]
    if failed:
        print(f"SUMMARY: {len(failed)}/{len(results)} check(s) failed.")
        sys.exit(1)
    else:
        print(f"SUMMARY: All {len(results)} check(s) passed.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="SSH availability and health check for a telecom node."
    )
    parser.add_argument("--host",     required=True,
                        help="Target node hostname or IP address")
    parser.add_argument("--user",     required=True,
                        help="SSH username")
    parser.add_argument("--key",      default=None,
                        help="Path to private key file")
    parser.add_argument("--password", default=None,
                        help="SSH password (prefer key-based auth)")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Run commands locally — no SSH connection made")
    args = parser.parse_args()

    is_local = args.dry_run or args.host in {"localhost", "127.0.0.1"}
    results: list[NodeCheckResult] = []

    if is_local:
        print(f"[DRY-RUN] Running local diagnostics (target would be {args.host})")
        for label, cmd in DIAG_COMMANDS:
            results.append(run_local(label, cmd))
    else:
        print(f"[SSH] Connecting to {args.user}@{args.host} …")
        for label, cmd in DIAG_COMMANDS:
            results.append(
                run_remote(args.host, args.user, args.key, args.password, label, cmd)
            )

    print_report(results, target=args.host)


if __name__ == "__main__":
    main()
