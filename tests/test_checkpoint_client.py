"""Tests for the simulated Check Point Management API client."""

from scripts.checkpoint_api_client import (
    CheckPointApiClient,
    FirewallRule,
    MockCheckPointServer,
    ValidationFinding,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def make_client() -> CheckPointApiClient:
    return CheckPointApiClient(host="mock", user="admin", password="secret",
                               verify_ssl=False)


def make_session():
    return MockCheckPointServer().build_session()


# ---------------------------------------------------------------------------
# Login / logout
# ---------------------------------------------------------------------------

def test_login_returns_true_with_mock():
    client = make_client()
    assert client.login(make_session()) is True


def test_logout_clears_token():
    client = make_client()
    session = make_session()
    client.login(session)
    client.logout(session)
    assert client._token is None


# ---------------------------------------------------------------------------
# Rule retrieval
# ---------------------------------------------------------------------------

def test_get_access_rules_returns_list():
    client = make_client()
    session = make_session()
    client.login(session)
    rules = client.get_access_rules(session)
    assert isinstance(rules, list)
    assert len(rules) == 3


def test_rules_have_expected_fields():
    client = make_client()
    session = make_session()
    client.login(session)
    rules = client.get_access_rules(session)
    for rule in rules:
        assert isinstance(rule, FirewallRule)
        assert rule.rule_id
        assert rule.action in {"Accept", "Drop"}


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

def test_clean_rules_produce_no_findings():
    rules = [
        FirewallRule("r1", "NOC_Network", "AVEIRO-5G-001", 22, "TCP", "Accept"),
        FirewallRule("r2", "MONITORING",  "AVEIRO-5G-002", 443, "TCP", "Accept"),
    ]
    findings = CheckPointApiClient.validate_rules(rules)
    assert findings == []


def test_public_ssh_is_flagged_as_high():
    rules = [FirewallRule("r1", "Any", "AVEIRO-5G-001", 22, "TCP", "Accept")]
    findings = CheckPointApiClient.validate_rules(rules)
    assert any(f.severity == "HIGH" for f in findings)
    assert any("SSH" in f.message for f in findings)


def test_telnet_is_flagged_as_medium():
    rules = [FirewallRule("r1", "NOC", "AVEIRO-5G-001", 23, "TCP", "Accept")]
    findings = CheckPointApiClient.validate_rules(rules)
    assert any(f.severity == "MEDIUM" for f in findings)
    assert any("Telnet" in f.message for f in findings)


def test_any_to_any_accept_is_flagged_as_high():
    rules = [FirewallRule("r1", "Any", "Any", 80, "TCP", "Accept")]
    findings = CheckPointApiClient.validate_rules(rules)
    assert any(f.severity == "HIGH" for f in findings)


def test_mock_policy_contains_one_finding():
    """End-to-end: the built-in mock policy has one bad rule (Telnet Any→Any)."""
    client = make_client()
    session = make_session()
    client.login(session)
    rules    = client.get_access_rules(session)
    findings = client.validate_rules(rules)
    # Rule-003 is Any→Any Telnet — should produce at least one finding
    assert len(findings) >= 1
    client.logout(session)
