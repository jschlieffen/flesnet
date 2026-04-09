#include <chrono>
#include <iostream>

// System dependent header files:
#include <sysexits.h>

// Boost Library header files:
#include <boost/program_options.hpp>
#include <tuple>

// Flesnet Library header files:
#include "lib/fles_ipc/MicrosliceOutputArchive.hpp"
#include "lib/fles_ipc/TimesliceAutoSource.hpp"


struct timeslice_sources_options {
  timeslice_sources_options(int argc, char* argv[]) { parse_options(argc, argv); }
  void parse_options(int argc, char* argv[]);

  std::vector<std::string> inputs;
  //std::string output;
};

class timeslice_sources_class{

    public:
        void Application(const std::vector<std::string>& inputs);
            static boost::program_options::options_description
            optionsDescription();
};