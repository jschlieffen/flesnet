
#include "Parameters.hpp"
#include "GitRevision.hpp"
#include "log.hpp"
#include <boost/program_options.hpp>
#include <boost/program_options/options_description.hpp>
#include <boost/program_options/variables_map.hpp>
#include <iostream>
#include <ostream>

namespace po = boost::program_options;

void Parameters::parse_options(int argc, char* argv[]){
    unsigned log_level = 2;
    unsigned log_syslog = 2;
    std::string log_file;
    std::stringstream desc_sstr;
    //TODO: desc string anpassen
    desc_sstr << std::endl
        << "Usage:"<<std::endl
        << "\t dtsatool -i input1.tsa [input2.tsa] -o output_folder"<<std::endl <<std::endl
        << "This program reads the given tsa files and write the descriptors timeslices, timeslicecomponents and microslices"
        << " into a seperat file" <<std::endl
        << "It can also create dtsa files without an input ms-Archive. For this execute:"<<std::endl<<std::endl
        << "\t dtsatool -d 1 -O output.dtsa"<<std::endl<<std::endl
        << "This line will create an dtsa file for 10000 ts and timeslice-size 100 where each microslice has the size of 1MB"<<std::endl
        << "Furthermore the program can transform .dtsa files in .dmsa files. For this execute:"<<std::endl<<std::endl
        << "\t dtsatool -D 1 -i input.dtsa";
    po::options_description general("General options");
    auto general_add = general.add_options();
    general_add("version,V","print version string");
    general_add("help,h","produce help message");

    po::options_description source("Source options");
    auto source_add = source.add_options();
    source_add("input-archives,i",po::value<std::vector<std::string>>(&input_archives_)
                                                ->multitoken(),
                    "name of an input file archive to read");

    po::options_description sink("Sink options");
    auto sink_add = sink.add_options();
    sink_add("output-folder,o",po::value<std::string>(&output_folder_)
                                                ->implicit_value(output_folder_),
            "name of an output folder to store the archives");
    sink_add("create-folder,c",po::value<bool>(&create_folder_)
                                                ->implicit_value(create_folder_),
            "decides whether the output-folder should be created");
    sink_add("output-archive,O",po::value<std::string>(&output_archive_)
                                                ->implicit_value(output_archive_),
            "name of an output archive to write");
    sink_add("create-dmsa,d",po::value<bool>(&create_dtsa_)
                                                ->implicit_value(create_dtsa_),
            "enable/disable if the dmsa-files should be created, rather than transformed");
    sink_add("dtsa2dmsa,D", po::value<bool>(&dtsa2dmsa_)
                                                ->implicit_value(dtsa2dmsa_),
            "enable/ disable if a dtsa should be transformed into a a dmsa");
    sink_add("components,C", po::value<uint64_t>(&components_)
                                                ->implicit_value(components_),
            "vector for the components of a timeslice. Microslices are distributed randomly");
    sink_add("timeslice-size,N", po::value<int>(&timeslice_size_)
                                                ->implicit_value(timeslice_size_),
            "Size of the timeslices");
    sink_add("num-ts,n",po::value<unsigned long>(&num_ts_)
                                                ->implicit_value(num_ts_),
            "gives the number of timeslices."
            "\nUsage only if you want to create new files");
    sink_add("contentsize-min,m",po::value<unsigned int>(&content_size_min_)
                                                ->implicit_value(content_size_min_),
            "gives the minimum content size of a microslice." 
            "\nUsage only if you want to create new files");
    sink_add("contentsize-max,M",po::value<unsigned int>(&content_size_max_)
                                                ->implicit_value(content_size_max_),
            "gives the maximum content size of a microslice." 
            "\nUsage only if you want to create new files");
    sink_add("maximum-number", po::value<uint64_t> (&maximum_number_)
                                                ->implicit_value(maximum_number_),
            "number of timeslices that should be processed");
    

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

}