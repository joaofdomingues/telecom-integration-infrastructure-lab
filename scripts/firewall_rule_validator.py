import argparse
import json


def validate_rules(policy: dict) -> list[str]:
    findings = []
    rules = policy.get("rules", [])

    for idx, rule in enumerate(rules, start=1):
        port = rule.get("port")
        source = rule.get("source")
        action = rule.get("action")

        if not isinstance(port, int) or port < 1 or port > 65535:
            findings.append(f"Rule {idx}: invalid port")

        if source == "PUBLIC" and port == 22 and action == "ALLOW":
            findings.append(f"Rule {idx}: public SSH access should not be allowed")

        if action not in {"ALLOW", "DENY"}:
            findings.append(f"Rule {idx}: invalid action")

    return findings


def main():
    parser = argparse.ArgumentParser(description="Validate simulated Check Point firewall rules")
    parser.add_argument("--rules", required=True, help="Path to firewall_rules.json")
    args = parser.parse_args()

    with open(args.rules, "r", encoding="utf-8") as file:
        policy = json.load(file)

    findings = validate_rules(policy)

    print(f"Policy: {policy.get('policy_name', 'unknown')}")
    if not findings:
        print("Firewall policy validation: OK")
    else:
        print("Firewall policy validation: CHECK REQUIRED")
        for finding in findings:
            print(f"- {finding}")


if __name__ == "__main__":
    main()
