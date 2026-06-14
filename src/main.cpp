#include "config_parser.h"
#include "integration_report.h"
#include "network_validator.h"

#include <algorithm>
#include <atomic>
#include <csignal>
#include <iostream>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <thread>
#include <vector>

// ---------------------------------------------------------------------------
// Graceful shutdown flag — set by SIGTERM / SIGINT
// ---------------------------------------------------------------------------
static std::atomic<bool> g_shutdown{false};

static void handleSignal(int) {
    g_shutdown.store(true, std::memory_order_relaxed);
}

// ---------------------------------------------------------------------------
// ValidationWorker — validates one node in its own thread
//
// Demonstrates:
//   • std::thread for parallel node validation
//   • std::mutex + std::lock_guard for result aggregation
//   • std::unique_ptr for RAII ownership of each worker
// ---------------------------------------------------------------------------
class ValidationWorker {
public:
    explicit ValidationWorker(const TelecomNode& node) : node_(node) {}

    // Non-copyable
    ValidationWorker(const ValidationWorker&)            = delete;
    ValidationWorker& operator=(const ValidationWorker&) = delete;

    void run(std::vector<ValidationResult>& results,
             std::mutex&                   resultsMutex) {
        thread_ = std::thread([this, &results, &resultsMutex]() {
            ValidationResult r = validate_node(node_);
            std::lock_guard<std::mutex> lock(resultsMutex);
            results.push_back(std::move(r));
        });
    }

    void join() {
        if (thread_.joinable()) thread_.join();
    }

    ~ValidationWorker() { join(); }   // RAII: join on destruction

private:
    TelecomNode node_;
    std::thread thread_;
};

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------
namespace {

struct CliArgs {
    std::string csvPath;
    bool        parallel{true};    // --serial disables parallel validation
    bool        help{false};
};

CliArgs parseArgs(int argc, char* argv[]) {
    CliArgs args;
    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        if (a == "--serial")            args.parallel = false;
        else if (a == "--help" || a == "-h") args.help = true;
        else if (a[0] != '-')           args.csvPath  = a;
    }
    return args;
}

void printHelp() {
    std::cout
        << "Usage: ./telecom_integration_checker <nodes.csv> [options]\n\n"
        << "Options:\n"
        << "  --serial   Validate nodes sequentially (default: parallel)\n"
        << "  --help     Show this help\n\n"
        << "Exit codes:\n"
        << "  0   All nodes READY_FOR_INTEGRATION\n"
        << "  1   Runtime error\n"
        << "  2   One or more nodes CHECK_REQUIRED\n";
}

} // namespace

// ---------------------------------------------------------------------------
// main
// ---------------------------------------------------------------------------
int main(int argc, char* argv[]) {
    std::signal(SIGTERM, handleSignal);
    std::signal(SIGINT,  handleSignal);

    const CliArgs args = parseArgs(argc, argv);
    if (args.help)         { printHelp(); return 0; }
    if (args.csvPath.empty()) {
        std::cerr << "Error: CSV path required. Use --help for usage.\n";
        return 1;
    }

    try {
        const auto nodes = load_nodes_from_csv(args.csvPath);

        std::vector<ValidationResult> results;
        results.reserve(nodes.size());

        if (args.parallel) {
            // ── Parallel validation — one thread per node ──────────────────
            std::mutex resultsMutex;
            std::vector<std::unique_ptr<ValidationWorker>> workers;
            workers.reserve(nodes.size());

            for (const auto& node : nodes) {
                if (g_shutdown.load()) break;
                workers.push_back(std::make_unique<ValidationWorker>(node));
                workers.back()->run(results, resultsMutex);
            }
            // RAII: workers' destructors join all threads
            workers.clear();
        } else {
            // ── Sequential validation ──────────────────────────────────────
            for (const auto& node : nodes) {
                if (g_shutdown.load()) break;
                results.push_back(validate_node(node));
            }
        }

        print_report(results);

        const bool allReady = std::all_of(
            results.begin(), results.end(),
            [](const ValidationResult& r) {
                return r.status == "READY_FOR_INTEGRATION";
            });

        return allReady ? 0 : 2;

    } catch (const std::exception& ex) {
        std::cerr << "Fatal error: " << ex.what() << "\n";
        return 1;
    }
}
