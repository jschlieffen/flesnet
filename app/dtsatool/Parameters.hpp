#pragma once

#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

/// Run parameter exception class.
class ParametersException : public std::runtime_error {
public:
  explicit ParametersException(const std::string& what_arg = "")
      : std::runtime_error(what_arg) {}
};

/// Global run parameter class.
class Parameters {
public:
  Parameters(int argc, char* argv[]) { parse_options(argc, argv); }

  Parameters(const Parameters&) = delete;
  void operator=(const Parameters&) = delete;

  [[nodiscard]] std::vector<std::string> input_archives() const { return input_archives_ ;}

  [[nodiscard]] std::string output_folder() const { return output_folder_; }

  [[nodiscard]] std::string output_archive() const { return output_archive_; }

  [[nodiscard]] bool create_folder() const { return create_folder_; }

  [[nodiscard]] bool create_dtsa() const { return create_dtsa_; }

  [[nodiscard]] bool dtsa2dmsa() const { return dtsa2dmsa_; }

  [[nodiscard]] uint64_t components() const { return components_; }

  [[nodiscard]] int timeslice_size() const { return timeslice_size_; }

  [[nodiscard]] unsigned long num_ts() const { return num_ts_; }

  [[nodiscard]] unsigned int content_size_min() const { return content_size_min_; }

  [[nodiscard]] unsigned int content_size_max() const { return content_size_max_; }

  [[nodiscard]] uint64_t maximum_number() const { return maximum_number_; }

private:
  void parse_options(int argc, char* argv[]);

    std::vector<std::string> input_archives_;
    std::string output_folder_;
    std::string output_archive_;
    bool create_folder_ = 0;
    bool create_dtsa_ = 0;
    bool dtsa2dmsa_ = 0; //weiss nicht ob ich das so drinne lasse 
    uint64_t components_ = 1;
    int timeslice_size_ = 100;
    unsigned long num_ts_ = 10000;
    unsigned int content_size_min_ = 1000000;
    unsigned int content_size_max_ = 1000000;
    uint64_t maximum_number_ = UINT64_MAX;
};
