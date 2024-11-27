#pragma once

#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

/// Run parameters exception class.
class ParametersException : public std::runtime_error {
public:
  explicit ParametersException(const std::string& what_arg = "")
      : std::runtime_error(what_arg) {}
};

struct Parameters {
    Parameters(int argc, char* argv[]) { parse_options(argc, argv); }
    void parse_options(int argc, char* argv[]);

    std::vector<std::string> input_archives;
    std::string output_folder;
    std::string output_archive;
    bool create_folder = 0;
    bool create_dmsa = 0;
    unsigned long num_ms = 10000;
    unsigned int content_size_min = 1000000;
    unsigned int content_size_max = 1000000;
};