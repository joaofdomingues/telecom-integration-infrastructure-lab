#pragma once

#include "config_parser.h"
#include <string>

// ---------------------------------------------------------------------------
// ValidationResult — outcome of validating one TelecomNode
// ---------------------------------------------------------------------------
struct ValidationResult {
    std::string node_id;
    bool        ip_valid{false};
    bool        ssh_port_valid{false};
    bool        latency_within_threshold{false};
    std::string status;      // "READY_FOR_INTEGRATION" | "CHECK_REQUIRED"
    std::string detail;      // human-readable reason when CHECK_REQUIRED
};

// Validate IPv4 address format using std::regex.
bool is_valid_ipv4(const std::string& ip);

// Validate a single telecom node and return a ValidationResult.
// Thread-safe: reads node by value, has no shared mutable state.
ValidationResult validate_node(const TelecomNode& node);
