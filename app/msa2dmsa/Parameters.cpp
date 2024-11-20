
#include "Parameters.hpp"
#include "GitRevision.hpp"
#include "log.hpp"
#include <boost/program_options.hpp>
#include <boost/program_options/options_description.hpp>
#include <boost/program_options/variables_map.hpp>
#include <iostream>

namespace po = boost::program_options;

void Parameters::parse_options(int argc, char* argv[]){
    unsigned log_level = 2;
    unsigned log_syslog = 2;
    std::string log_file;
    std::stringstream desc_sstr;
    desc_sstr << std::endl
        << "Usage:"<<std::endl
        << "\t msa2dmsa -i input1.msa [input2.msa] -o output_folder"<<std::endl <<std::endl
        << "This program reads the given msa files and write the descriptors into a seperat file" <<std::endl;
    po::options_description general("General options");
    auto general_add = general.add_options();
    general_add("version,V","print version string");
    general_add("help,h","produce help message");

    po::options_description source("Source options");
    auto source_add = source.add_options();
    source_add("input-archives,i",po::value<std::vector<std::string>>(&input_archives)
                                                ->multitoken(),
                    "name of an input file archive to read");

    po::options_description sink("Sink options");
    auto sink_add = sink.add_options();
    sink_add("output-folder,o",po::value<std::string>(&output_folder)
                                                ->implicit_value(output_folder),
            "name of an output file archive to write");
    sink_add("create-folder,c",po::value<bool>(&create_folder)
                                                ->implicit_value(create_folder),
                "decides whether the output-folder should be created");
    

    po::options_description desc(desc_sstr.str());
    desc.add(general).add(source).add(sink);

    po::variables_map vm;
    po::store(po::parse_command_line(argc, argv, desc),vm);
    po::notify(vm);

    if (vm.count("help") != 0u){
        std::cout << "mstool, git revision " << g_GIT_REVISION << std::endl;
        std::cout << desc << std::endl;
        exit(EXIT_SUCCESS);
    }

    if (vm.count("version") != 0u) {
        std::cout << "mstool " << g_PROJECT_VERSION_GIT << ", git revision "
            << g_GIT_REVISION << std::endl;
        exit(EXIT_SUCCESS);
    }

    logging::add_console(static_cast<severity_level>(log_level));
    if (vm.count("log-file") != 0u) {
        L_(info) << "Logging output to " << log_file;
        logging::add_file(log_file, static_cast<severity_level>(log_level));
    }
    if (vm.count("log-syslog") != 0u) {
        logging::add_syslog(logging::syslog::local0,
                        static_cast<severity_level>(log_syslog));

    }
    size_t input_sources = vm.count("input-archives");
    if (input_sources == 0) {
        throw ParametersException("no input source specified");
    }
    if (input_sources > 1) {
        throw ParametersException("more than one input source specified");
    }
}