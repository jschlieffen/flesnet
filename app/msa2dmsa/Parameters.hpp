#pragma once

#include <cstdint>
#include <stdexcept>
#include <string>

/// Run parameters exception class.
class ParametersException : public std::runtime_error {
public:
  explicit ParametersException(const std::string& what_arg = "")
      : std::runtime_error(what_arg) {}
};

struct Parameters {
    Parameters(int argc, char* argv[]) { parse_options(argc, argv); }
    void parse_options(int argc, char* argv[]);

    std::string input_archive;

    std::string output_archive;
};