#ifndef COMMANDLINEPARSER_HPP
#define COMMANDLINEPARSER_HPP

#include <sstream>

#include "options.hpp"

class commandLineParser {

public:
  options& opts;

  boost::program_options::options_description generic;
  boost::program_options::options_description hidden;
  boost::program_options::options_description visible;
  boost::program_options::options_description all;

  boost::program_options::options_description tsaReader;
  boost::program_options::options_description msaWriter;

  boost::program_options::positional_options_description positional;

  boost::program_options::variables_map vm;

  bool parsingError;

public:
  /**
   * @brief Show help message
   *
   * @details This function prints the help message to the standard output
   * stream. The information is printed in a way that is consistent with
   * whether the user asked for verbose output.
   */
  void showHelp(std::ostream& out) const;

  std::string getUsage() const;
  void checkForLogicErrors();

  unsigned int numParsedOptions() const;

  bool parse(int argc, char* argv[], std::vector<std::string>& errorMessage);

  commandLineParser(options& opts);
  ~commandLineParser() = default;

private:
  // Delete other constructors:
  commandLineParser() = delete;
  commandLineParser(const commandLineParser&) = delete;
  commandLineParser(commandLineParser&&) = delete;
  commandLineParser& operator=(const commandLineParser&) = delete;
  commandLineParser& operator=(commandLineParser&&) = delete;
};

#endif // COMMANDLINEPARSER_HPP
