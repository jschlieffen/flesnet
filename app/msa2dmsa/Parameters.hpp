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
    bool create_folder;
};