#include "integration_report.h"
#include <iomanip>
#include <iostream>

void print_report(const std::vector<ValidationResult>& results) {
    const int w1 = 18, w2 = 7, w3 = 7, w4 = 8;

    std::cout << "\nTELECOM INTEGRATION VALIDATION REPORT\n"
              << "======================================\n"
              << std::left
              << std::setw(w1) << "Node"
              << std::setw(w2) << "IP"
              << std::setw(w3) << "SSH"
              << std::setw(w4) << "Latency"
              << "Status\n"
              << std::string(72, '-') << "\n";

    int ready = 0, check = 0;
    for (const auto& r : results) {
        const std::string statusLabel =
            r.status == "READY_FOR_INTEGRATION" ? "READY_FOR_INTEGRATION"
                                                : "CHECK_REQUIRED";
        std::cout << std::left
                  << std::setw(w1) << r.node_id
                  << std::setw(w2) << (r.ip_valid   ? "OK"   : "FAIL")
                  << std::setw(w3) << (r.ssh_port_valid ? "OK" : "FAIL")
                  << std::setw(w4) << (r.latency_within_threshold ? "OK" : "WARN")
                  << statusLabel << "\n";

        if (!r.detail.empty())
            std::cout << std::string(w1 + w2 + w3 + w4, ' ')
                      << "  → " << r.detail << "\n";

        r.status == "READY_FOR_INTEGRATION" ? ++ready : ++check;
    }

    std::cout << std::string(72, '-') << "\n"
              << "Summary: " << ready << " ready, " << check << " check required.\n\n";
}
