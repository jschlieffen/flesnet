#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <tuple>
#include <boost/program_options.hpp>
#include <typeinfo>
#include "memory_test.hpp"
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
    memory_test_options options (argc,argv);
    memory_test_class foo;
    std::vector<std::tuple<int,int>> data;

    if (options.AutoVSManuell){
        data = foo.initAutoSource(options.inputs);

    }
    else{
        if (check_input_data(options.inputs)){
            data = foo.initManuellSource(options.inputs);
        }
        else{
            std::cout<<"wrong input" << std::endl;
        }
    
    }
    std::ofstream myfile(options.output);
    for (auto it : data){
        myfile << std::get<0>(it) << ","<< std::get<1>(it) << "\n";
    }
    myfile.close();
    return 0;


}