#pragma once
#include <string>
#include <vector>

struct TelecomNode {
    std::string node_id;
    std::string technology;
    std::string ip_address;
    int ssh_port;
    std::string service_name;
    int expected_latency_ms;
};

std::vector<TelecomNode> load_nodes_from_csv(const std::string& file_path);
