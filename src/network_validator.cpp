#include "network_validator.h"
#include <regex>
#include <sstream>

bool is_valid_ipv4(const std::string& ip) {
    const std::regex pattern(
        R"(^((25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})\.){3}(25[0-5]|2[0-4][0-9]|1?[0-9]{1,2})$)"
    );
    return std::regex_match(ip, pattern);
}

ValidationResult validate_node(const TelecomNode& node) {
    ValidationResult result;
    result.node_id = node.node_id;

    result.ip_valid              = is_valid_ipv4(node.ip_address);
    result.ssh_port_valid        = node.ssh_port > 0 && node.ssh_port <= 65535;
    result.latency_within_threshold = node.expected_latency_ms <= 50;

    if (result.ip_valid && result.ssh_port_valid && result.latency_within_threshold) {
        result.status = "READY_FOR_INTEGRATION";
    } else {
        result.status = "CHECK_REQUIRED";

        // Build a human-readable detail string
        std::ostringstream oss;
        if (!result.ip_valid)
            oss << "Invalid IPv4 (" << node.ip_address << "). ";
        if (!result.ssh_port_valid)
            oss << "Invalid SSH port (" << node.ssh_port << "). ";
        if (!result.latency_within_threshold)
            oss << "Latency " << node.expected_latency_ms << "ms exceeds 50ms threshold.";
        result.detail = oss.str();
    }

    return result;
}
