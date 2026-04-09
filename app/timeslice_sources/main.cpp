#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <tuple>
#include <boost/program_options.hpp>
#include <typeinfo>
//#include "memory_test.hpp"
#include "timeslice_sources.hpp"
#include <sys/resource.h>
//#include "plotting.hpp"


bool check_input_data(std::vector<std::string> inputs){
    for (const auto& input : inputs) {
        // This is a very simple check that triggers even if the special
        // characters are escaped, but since it only triggers a warning,
        // it is acceptable for now.
        if (input.find("%n") != std::string::npos) {
            return 0;
        }
    }
    return 1;


};
int main(int argc, char* argv[]){
    timeslice_sources_options options (argc,argv);
    timeslice_sources_class foo;
    //std::vector<std::tuple<int,int>> data;

    foo.Application(options.inputs);
    return 0;


}