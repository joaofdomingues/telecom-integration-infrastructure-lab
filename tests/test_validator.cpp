// test_validator.cpp — CTest coverage for network_validator + parallel worker
//
// Tests:
//  1.  Valid IPv4 passes
//  2.  Invalid IPv4 fails
//  3.  Valid SSH port passes
//  4.  Port 0 fails
//  5.  Port 70000 fails
//  6.  Latency at threshold passes
//  7.  Latency one above threshold warns
//  8.  All-OK node → READY_FOR_INTEGRATION
//  9.  Bad IP node → CHECK_REQUIRED
//  10. Detail string is non-empty on CHECK_REQUIRED
//  11. Thread-safety: 20 nodes validated in parallel, results count matches

#include "network_validator.h"
#include <atomic>
#include <cassert>
#include <iostream>
#include <mutex>
#include <thread>
#include <vector>

static TelecomNode goodNode() {
    return {"AVEIRO-5G-001", "5G", "192.168.10.21", 22, "small-cell", 18};
}

static void test_valid_ipv4() {
    assert(is_valid_ipv4("192.168.10.21"));
    assert(is_valid_ipv4("10.0.0.1"));
    assert(is_valid_ipv4("255.255.255.255"));
    std::cout << "[PASS] valid IPv4\n";
}

static void test_invalid_ipv4() {
    assert(!is_valid_ipv4("999.168.10.40"));
    assert(!is_valid_ipv4("192.168.10"));
    assert(!is_valid_ipv4("not-an-ip"));
    std::cout << "[PASS] invalid IPv4\n";
}

static void test_valid_ssh_port() {
    auto n = goodNode(); n.ssh_port = 22;
    assert(validate_node(n).ssh_port_valid);
    std::cout << "[PASS] valid SSH port\n";
}

static void test_port_zero_fails() {
    auto n = goodNode(); n.ssh_port = 0;
    assert(!validate_node(n).ssh_port_valid);
    std::cout << "[PASS] port 0 invalid\n";
}

static void test_port_overflow_fails() {
    auto n = goodNode(); n.ssh_port = 70000;
    assert(!validate_node(n).ssh_port_valid);
    std::cout << "[PASS] port 70000 invalid\n";
}

static void test_latency_at_threshold() {
    auto n = goodNode(); n.expected_latency_ms = 50;
    assert(validate_node(n).latency_within_threshold);
    std::cout << "[PASS] latency at threshold\n";
}

static void test_latency_above_threshold() {
    auto n = goodNode(); n.expected_latency_ms = 51;
    assert(!validate_node(n).latency_within_threshold);
    std::cout << "[PASS] latency above threshold\n";
}

static void test_ready_status() {
    assert(validate_node(goodNode()).status == "READY_FOR_INTEGRATION");
    std::cout << "[PASS] READY_FOR_INTEGRATION\n";
}

static void test_check_required_status() {
    auto n = goodNode(); n.ip_address = "999.0.0.1";
    assert(validate_node(n).status == "CHECK_REQUIRED");
    std::cout << "[PASS] CHECK_REQUIRED\n";
}

static void test_detail_non_empty_on_failure() {
    auto n = goodNode(); n.ip_address = "bad-ip"; n.ssh_port = 0;
    const auto r = validate_node(n);
    assert(!r.detail.empty());
    std::cout << "[PASS] detail string non-empty on failure\n";
}

static void test_parallel_validation() {
    // Validates 20 nodes concurrently and checks all results are collected.
    std::vector<TelecomNode> nodes;
    for (int i = 0; i < 20; ++i) {
        nodes.push_back({"NODE-" + std::to_string(i), "5G",
                         "192.168.10." + std::to_string(i + 1),
                         22, "sc", 20});
    }

    std::vector<ValidationResult> results;
    std::mutex mtx;
    std::vector<std::thread> threads;

    for (const auto& node : nodes) {
        threads.emplace_back([&node, &results, &mtx]() {
            auto r = validate_node(node);
            std::lock_guard<std::mutex> lock(mtx);
            results.push_back(std::move(r));
        });
    }
    for (auto& t : threads) t.join();

    assert(results.size() == 20);
    for (const auto& r : results)
        assert(r.status == "READY_FOR_INTEGRATION");

    std::cout << "[PASS] parallel validation (20 threads)\n";
}

int main() {
    test_valid_ipv4();
    test_invalid_ipv4();
    test_valid_ssh_port();
    test_port_zero_fails();
    test_port_overflow_fails();
    test_latency_at_threshold();
    test_latency_above_threshold();
    test_ready_status();
    test_check_required_status();
    test_detail_non_empty_on_failure();
    test_parallel_validation();
    std::cout << "\nAll validator tests passed.\n";
    return 0;
}
