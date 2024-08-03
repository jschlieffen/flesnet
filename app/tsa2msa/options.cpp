#include "options.hpp"

genericOptions genericOptions::defaults() {
  genericOptions defaults;
  // [genericDefaults]
  defaults.beQuiet = false;
  defaults.beVerbose = false;
  defaults.showHelp = false;
  defaults.showVersion = false;
  // [genericDefaults]
  return defaults;
}

boost::program_options::options_description
genericOptions::optionsDescription(genericOptions& options) {
  boost::program_options::options_description desc("Generic options");
  desc.add_options()
      // clang-format off
      ("quiet,q",
        boost::program_options::bool_switch(&options.beQuiet),
        "suppress all output")
      ("verbose,v",
        boost::program_options::bool_switch(&options.beVerbose),
        "enable verbose output")
      ("help,h",
        boost::program_options::bool_switch(&options.showHelp),
        "produce help message\n"
        "  (combine with --verbose to see all options)")
      ("version,V",
        boost::program_options::bool_switch(&options.showVersion),
        "produce version message")
      // clang-format on
      ;
  return desc;
}

// clang-format off
options::options() :
  generic(genericOptions::defaults()),
  tsaReader(tsaReader::defaults()),
  msaWriter(msaWriter::defaults()),
  parsingError(false)
// clang-format on
{}

void options::parseCommandLine(
    int argc,
    char* argv[],
    const boost::program_options::options_description& command_line_options,
    boost::program_options::variables_map& vm,
    std::vector<std::string>& errorMessage) {

  boost::program_options::positional_options_description
      positional_command_line_arguments;
  // Specify that all positional arguments are input files:
  positional_command_line_arguments.add("input", -1);

  // Parse command line arguments and store them in a variables map
  try {
    // Since we are using positional arguments, we need to use the
    // command_line_parser instead of the parse_command_line
    // function, which only supports named options.
    boost::program_options::store(
        boost::program_options::command_line_parser(argc, argv)
            .options(command_line_options)
            .positional(positional_command_line_arguments)
            .run(),
        vm);
    boost::program_options::notify(vm);
  } catch (const boost::program_options::error& e) {
    errorMessage.push_back("Error: " + std::string(e.what()));
    parsingError = true;
  }
}

void options::handleErrors(
    const std::vector<std::string>& errorMessage,
    const boost::program_options::options_description& command_line_options,
    const boost::program_options::options_description&
        visible_command_line_options) {

  for (const auto& msg : errorMessage) {
    std::cerr << msg << std::endl;
  }

  if (!generic.showHelp) {
    // Otherwise, the user is expecting a help message, anyway.
    // So, we don't need to inform them about our decision to
    // show them usage information without having been asked.
    std::cerr << "Errors occurred: Printing usage." << std::endl << std::endl;
  }

  if (generic.beVerbose) {
    std::cerr << command_line_options << std::endl;
  } else {
    std::cerr << visible_command_line_options << std::endl;
  }

  if (generic.showHelp) {
    // There was a parsing error, which means that additional
    // options were provided.
    std::cerr << "Error: Ignoring any other options." << std::endl;
  }
}

void options::showHelp(
    const boost::program_options::options_description& command_line_options,
    const boost::program_options::options_description&
        visible_command_line_options) {
  if (generic.beVerbose) {
    std::cout << command_line_options << std::endl;
  } else {
    std::cout << visible_command_line_options << std::endl;
  }
}
