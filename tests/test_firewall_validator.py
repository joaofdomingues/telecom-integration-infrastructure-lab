from scripts.firewall_rule_validator import validate_rules


def test_valid_policy_has_no_findings():
    policy = {"rules": [{"source": "NOC", "destination": "NODE1", "port": 22, "protocol": "TCP", "action": "ALLOW"}]}
    assert validate_rules(policy) == []


def test_public_ssh_allow_is_flagged():
    policy = {"rules": [{"source": "PUBLIC", "destination": "NODE1", "port": 22, "protocol": "TCP", "action": "ALLOW"}]}
    findings = validate_rules(policy)
    assert any("public SSH" in finding for finding in findings)


def test_invalid_port_is_flagged():
    policy = {"rules": [{"source": "NOC", "destination": "NODE1", "port": 70000, "protocol": "TCP", "action": "ALLOW"}]}
    findings = validate_rules(policy)
    assert any("invalid port" in finding for finding in findings)
