//#include "memory_test.hpp"
#include "timeslice_sources.hpp"
#include "MergingSource.hpp"
#include "StorableMicroslice.hpp"
#include "StorableTimeslice.hpp"
#include "Timeslice.hpp"
#include "TimesliceInputArchive.hpp"
#include "TimesliceSource.hpp"
#include "TimesliceAutoSource.hpp"
#include <boost/program_options/options_description.hpp>
#include <chrono>
#include <memory>
#include <ratio>
#include<thread>
#include <tuple>
#include<typeinfo>
#include <sys/resource.h>
#include <vector>
#include "sys/types.h"
#include "sys/sysinfo.h"
#include "stdlib.h"
#include "stdio.h"
#include "string.h"
#include <ratio>
#include "GitRevision.hpp"
#include <malloc.h>
#include <iostream>


void timeslice_sources_options::parse_options(int argc, char* argv[]){

  std::stringstream desc_sstr;
  desc_sstr << std::endl
    << "Usage:" << std::endl
    << "\t timeslice_sources -i input1.tsa [ input2.tsa ... ] " << std::endl << std::endl
    << "Only for test purposes"
    << std::endl << std::endl
    << "Command line options";
  boost::program_options::options_description desc(desc_sstr.str());
    desc.add_options()
          ("version,V", "print version string")
          ("help,h", "produce help message")
          ("input-archives,i", boost::program_options::value<std::vector<std::string>>(&inputs)
                                            ->multitoken()
                                            ->value_name("<space-separated-tsa-files>"),
                    "Paths to input timeslice archives (.tsa).");
  boost::program_options::variables_map vm;
  boost::program_options::store(boost::program_options::parse_command_line(argc, argv, desc), vm);
  boost::program_options::notify(vm);
  logging::add_console(static_cast<severity_level>(1));
  if (vm.count("help") != 0u) {
    std::cout << "archive_validator, git revision " << g_GIT_REVISION << std::endl;
    std::cout << desc << std::endl;
    exit(EXIT_SUCCESS);
  }

  if (vm.count("version") != 0u) {
    std::cout << "archive_validator " << g_PROJECT_VERSION_GIT << ", git revision "
              << g_GIT_REVISION << std::endl;
    exit(EXIT_SUCCESS);
  }

};

void timeslice_sources_class::Application(const std::vector<std::string>& inputs){

    std::unique_ptr<fles::TimesliceSource> ts_source = std::make_unique<fles::TimesliceAutoSource> (inputs);
    while(std::shared_ptr<fles::Timeslice> timeslice =  ts_source->get()){
    std::shared_ptr<fles::Timeslice> timeslice_2 = ts_source->get();
    //std::shared_ptr<fles::Timeslice> timeslice_2 = timeslice;
    if (timeslice && timeslice_2) {
        std::cout<<"Both pointers are not null\n";
    }
    if (timeslice == timeslice_2) {
        std::cout << "Both shared_ptrs point to the same object\n";
    } else {
        std::cout << "Shared_ptrs point to different objects\n"<< timeslice << " "<<timeslice_2 <<std::endl;
        
    }
    std::cout<<"timeslice 1: "<<timeslice->index()<<std::endl;
    std::cout<<"timeslice 2: "<<timeslice_2->index()<<std::endl;
    }
}