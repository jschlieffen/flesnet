#include "memory_test.hpp"
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


//Programmoptions zum aufrufen des Programms muss folgende Zeile angegeben werden:
// ./memorytest -I input1 [input2] .. -O output.csv -A 0||1
// -I erwartet tsa-Dateien 
// -O erwartet eine csv Datei
// -A erwartet ein Bool ob ueber Timesliceautosource eingelesen werden soll oder manuell
//    1 fuer Timesliceautosource
//    0 fuer manuell
void memory_test_options::parse_options(int argc, char* argv[]){

  std::stringstream desc_sstr;
  desc_sstr << std::endl
    << "Usage:" << std::endl
    << "\t memory_test -I input1.tsa [ input2.tsa ... ] -O output.csv -A 1 || 0" << std::endl << std::endl
    << "This program checks the RAM usage of certain ways to read timeslice archive files and writes the data into a csv file" << std::endl
    << "Input data is defined by timeslice archives (*.tsa)." << std::endl
    << "Output data is defined by a csv file" << std::endl
    << "Use the python file plotting.py if you want to plot the data"
    << std::endl << std::endl
    << "Command line options";
  boost::program_options::options_description desc(desc_sstr.str());
    desc.add_options()
          ("version,V", "print version string")
          ("help,h", "produce help message")
          ("input-archives,I", boost::program_options::value<std::vector<std::string>>(&inputs)
                                            ->multitoken()
                                            ->value_name("<space-separated-tsa-files>"),
                    "Paths to input timeslice archives (.tsa).")
          ("output-csv,O", 
            boost::program_options::value<std::string>(&output),
            "path to output csv. If this file does not exists, the program will generate a new one"
          )
          ("AutoVSManuell,A", 
              boost::program_options::value<bool>(&AutoVSManuell),
              "decide how to read the input files. \nA = 1:   The program will use TimesliceAutosource  \nA = 0:    The programm will use the method of the archive validator"
          );

  boost::program_options::variables_map vm;
  boost::program_options::store(boost::program_options::parse_command_line(argc, argv, desc), vm);
  boost::program_options::notify(vm);

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


//together with get_mem_usage(), these two functions computes the used RAM-usage currently used by the application
//Documentation: https://stackoverflow.com/questions/63166/how-to-determine-cpu-and-memory-consumption-from-inside-a-process
//              Warning: This programm can only be used in Linux. For Windows and MacOS see. Documentation

int parseLine(char* line){
    // This assumes that a digit will be found and the line ends in " Kb".
    int i = strlen(line);
    const char* p = line;
    while (*p <'0' || *p > '9') p++;
    line[i-3] = '\0';
    i = atoi(p);
    return i;
}

int get_mem_usage(){ //Note: this value is in KB!
    FILE* file = fopen("/proc/self/status", "r");
    int result = -1;
    char line[128];

    while (fgets(line, 128, file) != NULL){
        if (strncmp(line, "VmRSS:", 6) == 0){
            result = parseLine(line);
            break;
        }
    }
    fclose(file);
    return result;
}

std::vector<std::tuple<int,int>> memory_test_class::initAutoSource(const std::vector<std::string>& inputs) {

  const auto t1 = std::chrono::high_resolution_clock::now();

  // reading of the timeslices with Timesliceautosource
  std::unique_ptr<fles::TimesliceSource> ts_source = std::make_unique<fles::TimesliceAutoSource> (inputs);
   //std::shared_ptr<const fles::Timeslice> current_ts = ts_source.get();
  std::shared_ptr<fles::Timeslice> next_ts = nullptr;
  
  // just a small check if the input has failed
  //if (current_ts == nullptr){
    //std::cout << "incorrect input" <<std::endl;
  //} 

  // this array consist the processing time and the RAM-usage
  std::vector<std::tuple<int,int>> res;
  std::cout<<"test2.1"<<std::endl;
  std::unique_ptr<const fles::Timeslice> test_ts = ts_source->get();
  std::cout<<"test2.2"<<std::endl;
  int memory_usage;
  // in this while-loop, the programm looks at every timeslice. After that the RAM-usage and the time is checked
  // and stored in the array res
  std::cout<<"test"<<std::endl;
  while(auto next_ts = ts_source->get()){
    std::cout<<"test1.1"<<std::endl;
    std::shared_ptr<const fles::Timeslice> current_ts;
    std::cout<<"test1.2"<<std::endl;
    current_ts = (std::move(next_ts));
    std::cout<<"test1.3"<<std::endl;
    next_ts.reset();
    std::cout<<"test1.4"<<std::endl;
    const auto t2 = std::chrono::high_resolution_clock::now();
    const auto current_time = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1);
    //std::cout<<typeid(current_time).name() <<std::endl;
    memory_usage = get_mem_usage()/1000;
    std::cout << "current_ts.use_count() = " << current_ts.use_count() << std::endl;

    res.push_back(std::make_tuple(current_time.count(),memory_usage));
    current_ts.reset();
    malloc_trim(0);
    }

  return res;
};

std::vector<std::tuple<int,int>>  memory_test_class::initManuellSource(const std::vector<std::string>& inputs){
  

  const auto t1 = std::chrono::high_resolution_clock::now();


  // reading of the timeslices via the source code of the achive validator
  std::vector<std::unique_ptr<fles::TimesliceSource>> ts_sources = {};
  for (auto p : inputs) {
      std::unique_ptr<fles::TimesliceSource> source =
          std::make_unique<fles::TimesliceInputArchive>(p);
      ts_sources.emplace_back(std::move(source));
  }  
  fles::MergingSource<fles::TimesliceSource> ts_source(std::move(ts_sources));
  std::shared_ptr<fles::Timeslice> next_ts = nullptr;
  std::shared_ptr<fles::Timeslice> current_ts = ts_source.get();

  // just a small check if the input has failed 
  if (current_ts == nullptr){
    std::cout << "incorrect input" <<std::endl;
  } 

  // this array consist the processing time and the RAM-usage
  std::vector<std::tuple<int,int>> res;
  int memory_usage;

  // in this while-loop, the programm looks at every timeslice. After that the RAM-usage and the time is checked
  // and stored in the array res
  while(next_ts != current_ts){
    //current_ts.reset();
    current_ts = next_ts;
    next_ts.reset();
    next_ts = ts_source.get(); 
    const auto t2 = std::chrono::high_resolution_clock::now();
    const auto current_time = std::chrono::duration_cast<std::chrono::milliseconds>(t2 - t1);
    memory_usage = get_mem_usage()/1000;

    res.push_back(std::make_tuple(current_time.count(),memory_usage));

  }

  return res;
};
