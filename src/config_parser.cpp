#include "config_parser.h"
#include <fstream>
#include <sstream>
#include <stdexcept>

std::vector<TelecomNode> load_nodes_from_csv(const std::string& file_path) {
    std::ifstream file(file_path);
    if (!file.is_open()) {
        throw std::runtime_error("Unable to open config file: " + file_path);
    }

    std::vector<TelecomNode> nodes;
    std::string line;
    bool first_line = true;

    while (std::getline(file, line)) {
        if (line.empty()) continue;
        if (first_line) {
            first_line = false;
            continue;
        }

        std::stringstream ss(line);
        std::string item;
        std::vector<std::string> fields;

        while (std::getline(ss, item, ',')) {
            fields.push_back(item);
        }

        if (fields.size() != 6) {
            continue;
        }

        TelecomNode node;
        node.node_id = fields[0];
        node.technology = fields[1];
        node.ip_address = fields[2];
        node.ssh_port = std::stoi(fields[3]);
        node.service_name = fields[4];
        node.expected_latency_ms = std::stoi(fields[5]);
        nodes.push_back(node);
    }

    return nodes;
}
