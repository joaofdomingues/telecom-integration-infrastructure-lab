"""
checkpoint_api_client.py — Simulated Check Point Management API client.

Demonstrates the workflow used to interact with a real Check Point Security
Management Server (SMS) REST API:
  1. Authenticate  →  receive session token
  2. Fetch policy  →  retrieve access rules
  3. Validate      →  check rules against a security baseline
  4. Logout        →  invalidate session

In this portfolio project the HTTP calls are intercepted by a mock server
(see MockCheckPointServer) so no real Check Point appliance is needed.
The same CheckPointApiClient class would work against a real SMS by
passing a real host/credentials and removing the mock layer.

Usage:
  python scripts/checkpoint_api_client.py
  python scripts/checkpoint_api_client.py --host 192.168.1.100 --user admin --password secret
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class FirewallRule:
    rule_id:     str
    source:      str
    destination: str
    port:        int
    protocol:    str
    action:      str


@dataclass
class ValidationFinding:
    rule_id:  str
    severity: str   # "HIGH" | "MEDIUM" | "INFO"
    message:  str


# ---------------------------------------------------------------------------
# Check Point API Client
# ---------------------------------------------------------------------------

class CheckPointApiClient:
    """Minimal client for the Check Point Management REST API.

    Reference: Check Point R81.20 Management API Guide, Chapter 3.
    Real endpoint:  https://<sms-host>/web_api/
    """

    def __init__(self, host: str, user: str, password: str,
                 port: int = 443, verify_ssl: bool = True) -> None:
        self.base_url   = f"https://{host}:{port}/web_api"
        self.user       = user
        self.password   = password
        self.verify_ssl = verify_ssl
        self._token: str | None = None

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def login(self, session: Any) -> bool:
        """POST /web_api/login and store the session token."""
        payload = {"user": self.user, "password": self.password}
        response = session.post(
            f"{self.base_url}/login",
            json=payload,
            verify=self.verify_ssl,
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        self._token = data.get("sid")
        return bool(self._token)

    def logout(self, session: Any) -> None:
        """POST /web_api/logout to invalidate the session."""
        if not self._token:
            return
        session.post(
            f"{self.base_url}/logout",
            headers=self._auth_headers(),
            json={},
            verify=self.verify_ssl,
            timeout=10,
        )
        self._token = None

    # ------------------------------------------------------------------
    # Rule retrieval
    # ------------------------------------------------------------------

    def get_access_rules(self, session: Any,
                         layer: str = "Network") -> list[FirewallRule]:
        """POST /web_api/show-access-rulebase to retrieve rules."""
        payload = {"name": layer, "limit": 50, "details-level": "standard"}
        response = session.post(
            f"{self.base_url}/show-access-rulebase",
            headers=self._auth_headers(),
            json=payload,
            verify=self.verify_ssl,
            timeout=10,
        )
        response.raise_for_status()
        data   = response.json()
        rules  = data.get("rulebase", [])
        return [self._parse_rule(r) for r in rules]

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def validate_rules(rules: list[FirewallRule]) -> list[ValidationFinding]:
        """Apply a security baseline to a list of firewall rules."""
        findings: list[ValidationFinding] = []

        for rule in rules:
            # HIGH: SSH open to the public internet
            if (rule.source == "Any" and rule.port == 22
                    and rule.action == "Accept"):
                findings.append(ValidationFinding(
                    rule_id=rule.rule_id,
                    severity="HIGH",
                    message="Public SSH access (port 22 from Any) should be restricted.",
                ))

            # HIGH: Any-to-Any accept (overly permissive)
            if (rule.source == "Any" and rule.destination == "Any"
                    and rule.action == "Accept"):
                findings.append(ValidationFinding(
                    rule_id=rule.rule_id,
                    severity="HIGH",
                    message="Overly permissive rule: Any → Any Accept.",
                ))

            # MEDIUM: Telnet allowed (plaintext protocol)
            if rule.port == 23 and rule.action == "Accept":
                findings.append(ValidationFinding(
                    rule_id=rule.rule_id,
                    severity="MEDIUM",
                    message="Telnet (port 23) is a plaintext protocol; use SSH instead.",
                ))

        return findings

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        return {"X-chkp-sid": self._token or ""}

    @staticmethod
    def _parse_rule(raw: dict) -> FirewallRule:
        services = raw.get("service", [{}])
        port = services[0].get("port", 0) if services else 0
        return FirewallRule(
            rule_id     = raw.get("uid", "unknown"),
            source      = raw.get("source", [{}])[0].get("name", "Any"),
            destination = raw.get("destination", [{}])[0].get("name", "Any"),
            port        = port,
            protocol    = "TCP",
            action      = raw.get("action", {}).get("name", "Drop"),
        )


# ---------------------------------------------------------------------------
# Mock Check Point server (for demo / CI — no real appliance needed)
# ---------------------------------------------------------------------------

class MockCheckPointServer:
    """Returns canned API responses that mimic a real SMS."""

    MOCK_RULES = [
        {
            "uid": "rule-001",
            "source":      [{"name": "NOC_Network"}],
            "destination": [{"name": "AVEIRO-5G-001"}],
            "service":     [{"port": 22}],
            "action":      {"name": "Accept"},
        },
        {
            "uid": "rule-002",
            "source":      [{"name": "MONITORING"}],
            "destination": [{"name": "AVEIRO-5G-002"}],
            "service":     [{"port": 443}],
            "action":      {"name": "Accept"},
        },
        {
            "uid": "rule-003",           # Intentionally bad rule for demo
            "source":      [{"name": "Any"}],
            "destination": [{"name": "Any"}],
            "service":     [{"port": 23}],
            "action":      {"name": "Accept"},
        },
    ]

    def build_session(self) -> MagicMock:
        session = MagicMock()

        login_resp = MagicMock()
        login_resp.json.return_value = {"sid": "mock-session-token-abc123"}
        login_resp.raise_for_status = MagicMock()
        session.post.side_effect = self._dispatch

        return session

    def _dispatch(self, url: str, **kwargs) -> MagicMock:
        resp = MagicMock()
        resp.raise_for_status = MagicMock()

        if url.endswith("/login"):
            resp.json.return_value = {"sid": "mock-session-token-abc123"}
        elif url.endswith("/show-access-rulebase"):
            resp.json.return_value = {"rulebase": self.MOCK_RULES, "total": len(self.MOCK_RULES)}
        elif url.endswith("/logout"):
            resp.json.return_value = {"message": "OK"}
        else:
            resp.json.return_value = {}

        return resp


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Check Point API demo client")
    parser.add_argument("--host",     default="mock",
                        help="SMS host (default: mock — uses built-in mock server)")
    parser.add_argument("--user",     default="admin")
    parser.add_argument("--password", default="secret")
    args = parser.parse_args()

    use_mock = args.host == "mock"
    client   = CheckPointApiClient(
        host=args.host, user=args.user, password=args.password, verify_ssl=False
    )

    if use_mock:
        print("[INFO] Running in MOCK mode — no real Check Point appliance needed.")
        session = MockCheckPointServer().build_session()
    else:
        import requests
        session = requests.Session()

    # 1. Login
    ok = client.login(session)
    print(f"[LOGIN] {'OK' if ok else 'FAILED'}")

    # 2. Fetch rules
    rules = client.get_access_rules(session)
    print(f"[RULES] Retrieved {len(rules)} access rule(s).")

    # 3. Validate
    findings = client.validate_rules(rules)
    if not findings:
        print("[VALIDATION] All rules passed the security baseline.")
    else:
        print(f"[VALIDATION] {len(findings)} finding(s):")
        for f in findings:
            print(f"  [{f.severity}] Rule {f.rule_id}: {f.message}")

    # 4. Logout
    client.logout(session)
    print("[LOGOUT] Session closed.")


if __name__ == "__main__":
    main()
