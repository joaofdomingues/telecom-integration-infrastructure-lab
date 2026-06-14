cmake_minimum_required(VERSION 3.14)
project(TelecomIntegrationChecker VERSION 2.0.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ---------------------------------------------------------------------------
# Cross-compilation
#   cmake .. -DTARGET_ARCH=aarch64
#            -DCMAKE_C_COMPILER=aarch64-linux-gnu-gcc
#            -DCMAKE_CXX_COMPILER=aarch64-linux-gnu-g++
# ---------------------------------------------------------------------------
option(TARGET_ARCH "Target architecture: native | aarch64" "native")

include_directories(src)
enable_testing()

# ---------------------------------------------------------------------------
# Core library
# ---------------------------------------------------------------------------
add_library(telecom_core
    src/config_parser.cpp
    src/network_validator.cpp
    src/integration_report.cpp
)

# Link pthreads for std::thread on Linux
find_package(Threads REQUIRED)
target_link_libraries(telecom_core Threads::Threads)

# ---------------------------------------------------------------------------
# Main executable
# ---------------------------------------------------------------------------
add_executable(telecom_integration_checker src/main.cpp)
target_link_libraries(telecom_integration_checker telecom_core)

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
add_executable(test_validator tests/test_validator.cpp)
target_link_libraries(test_validator telecom_core)
add_test(NAME validator_ctest COMMAND test_validator)
