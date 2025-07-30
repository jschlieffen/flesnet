
#include "Application.hpp"
#include "ManagedTimesliceBuffer.hpp"
#include "MicrosliceDescriptor.hpp"
#include "StorableTimeslice.hpp"
#include "StorableTimesliceDescriptor.hpp"
#include "TimesliceBuilder.hpp"
#include "MicrosliceDescribtorOutputArchive.hpp"
#include "Timeslice.hpp"
#include "TDescriptor.hpp"
#include "TimesliceAnalyzer.hpp"
#include "TimesliceAutoSource.hpp"
#include "TimesliceDescriptorAutoSource.hpp"
#include "TimesliceDebugger.hpp"
#include "TimesliceOutputArchive.hpp"
#include "TimesliceDescriptorOutputArchive.hpp"
#include "TimeslicePublisher.hpp"
#include "Utility.hpp"
#include "PatternGenerator.hpp"
#include <chrono>
#include <cstdint>
#include <memory>
#include <thread>
#include <utility>
#include <filesystem>

Application::Application(Parameters const& par) : par_(par){

    std::vector<std::string> output_archives;
    std::string output_string;
    if (!dirExists(par_.output_folder().c_str()) && par_.output_folder() != ""){
        if(par_.create_folder()){
            std::filesystem::create_directories(par_.output_folder());
        }
        else{
            throw std::ios_base::failure ("Folder do not exists. Use parameter create Folders to create them.");
        }
    }
    if (par_.dtsa2dmsa()){
            source_descriptors = std::make_unique<fles::TimesliceDescriptorAutoSource>(par_.input_archives());
    }
    else if (!par_.input_archives().empty()){
        for (auto input_archive : par_.input_archives()){
            sources_.push_back(std::make_shared<fles::TimesliceAutoSource>(input_archive));  
            output_string = std::filesystem::path(input_archive).filename().string();
            output_string.resize(output_string.find(".tsa"));
            output_string = par_.output_folder() +output_string + ".dtsa";
            output_archives.push_back(output_string);
        }
    }
        if (par_.create_dtsa()){
        uint64_t offset = 0;
        for (uint64_t i = 0; i <= par_.num_ts()*(par_.timeslice_size()-1); i++){
            generated_descriptors.push_back(std::make_shared<fles::MicrosliceDescriptor>(
                static_cast<fles::MicrosliceDescriptor>(PatternGenerator(i,
                                                                        par_.content_size_min(),
                                                                        par_.content_size_max(),
                                                                        offset))
                )
            );
            offset += generated_descriptors[i]->size;
        
        }
    }
    if (!output_archives.empty()){
        for (auto output_archive : output_archives){
            sinks_.push_back(std::shared_ptr<fles::TimesliceDescriptorSink>(
               new fles::TimesliceDescriptorOutputArchive(output_archive)));
        }
    }
    else if (!par_.output_archive().empty()){
        std::string output_archive = par_.output_folder() + par_.output_archive();
        sink = std::shared_ptr<fles::TimesliceDescriptorSink>(
               new fles::TimesliceDescriptorOutputArchive(output_archive));
    }

}

Application::~Application() {
  L_(info) << output_prefix_ << "total timeslices processed: " << count_;

  // delay to allow monitor to process pending messages
  constexpr auto destruct_delay = std::chrono::milliseconds(200);
  std::this_thread::sleep_for(destruct_delay);
}


int Application::dirExists(const char *path){
    struct stat info;
    if(stat(path, &info) != 0){ return 0;}
    else if(info.st_mode & S_IFDIR){ return 1;}
    else{ return 0; }
}

fles::TDescriptor Application::create_descriptor_ts(std::shared_ptr<const fles::Timeslice> ts){
  uint64_t ts_index = ts->index();
  uint64_t ts_pos = ts->tpos();
  uint64_t ts_num_corems = ts->num_core_microslices(); 
  fles::TDescriptor TD(ts_num_corems, ts_index,ts_pos);
  for (uint64_t tsc = 0; tsc < ts->num_components(); tsc++){
    uint64_t num_ms = ts->num_microslices(tsc);
    TD.append_component(num_ms);
    for (uint64_t msc = 0; msc < (ts-> num_microslices(tsc)); msc++){
      fles::MicrosliceDescriptor ms_desc= ts->descriptor(tsc,msc);
      TD.append_ms_desc(tsc, msc, ms_desc);
    }
  }
  return TD;
}

fles::TDescriptor Application::create_new_descriptor_ts(uint64_t ts_index, uint64_t ts_pos, 
                                                        uint64_t ts_num_corems, int i){
  fles::TDescriptor TD(ts_num_corems, ts_index,ts_pos);
  std::vector component_sizes(par_.components(), par_.timeslice_size()/par_.components());
  uint64_t remainder = par_.timeslice_size() % par_.components();
  for (uint64_t tsc = 0; tsc < par_.components(); tsc++){
    uint64_t num_ms;
    if (tsc < remainder){
        num_ms = component_sizes[tsc]++;
    }
    else{
        num_ms = component_sizes[tsc];
    }
    TD.append_component(num_ms);
    for (uint64_t msc = 0; msc < num_ms; msc++){
      fles::MicrosliceDescriptor ms_desc= *generated_descriptors[i];
      TD.append_ms_desc(tsc, msc, ms_desc);
      i += 1;
    }
  }
  return TD;
}


std::string compute_common_prefix(const std::vector<std::string>& strings) {
  std::string prefix; // default constructor initializes to empty string
  if (strings.size() == 0) {
    // If there are no strings, return an empty string
    return prefix;
  }

  // Initialize the prefix to the first string
  prefix = strings[0];

  // Iterate through the strings and truncate the prefix as needed
  for (const auto& input : strings) {

    // If the prefix is empty, there is no common prefix and we can stop
    if (prefix.size() == 0) {
      break;
    }

    if (input.size() < prefix.size()) {
      // If the input is shorter than the prefix, truncate the prefix
      // to the length of the input
      prefix = prefix.substr(0, input.size());
    }

    // Compare the prefix and the input, and truncate the prefix as
    // needed
    for (unsigned i = 0; i < prefix.size(); ++i) {
      if (prefix[i] != input[i]) {
        prefix = prefix.substr(0, i);
        break;
      }
    }
  }

  return prefix;
}

std::string Application::constructArchiveName(const fles::Subsystem& sys_id,
                                              const uint16_t& eq_id) {
  std::string prefix = compute_common_prefix(par_.input_archives());

  if (prefix.size() == 0) {
    std::cerr << "Error: Prefix is empty, should not happen."
              << " Setting arbitrary prefix." << std::endl;
    prefix = "empty_prefix";
  }
  std::string sys_id_string = fles::to_string(sys_id);
  // eq_id is a uint16_t, and most likely typedefed to some
  // primitive integer type, so likely implicit conversion to
  // that integer type is safe. However, the fixed width
  // integer types are implementation defined, so the correct
  // way to do this likely involves using the PRIu16 format
  // macro.
  std::string eq_id_string = std::to_string(eq_id);
  std::string msa_archive_name = prefix + "_" + sys_id_string + "_" +
                                 eq_id_string + ".dmsa";
  if (msaFiles.find(msa_archive_name) == msaFiles.end()) {
    std::unique_ptr<fles::Sink<fles::MicrosliceDescriptor>> msaFile;
    msaFile = std::make_unique<fles::MicrosliceDescriptorOutputArchive>(msa_archive_name);
    msaFiles[msa_archive_name] = std::move(msaFile);
  }
  return msa_archive_name;
}

void Application::dtsa2dmsa_writer(std::shared_ptr<fles::TDescriptor> TD){

    for (uint64_t tsc = 0; tsc < TD->num_components(); tsc++){
        for (uint64_t msc = 0; msc < TD->num_core_microslices(); msc++){
            fles::MicrosliceDescriptor msd= TD->descriptor(tsc,msc);
            const uint16_t& eq_id = msd.eq_id;
            const fles::Subsystem& sys_id = static_cast<fles::Subsystem>(msd.sys_id);
            std::string msa_archive_name = constructArchiveName(sys_id, eq_id);
            msaFiles[msa_archive_name]->put(std::make_shared<fles::MicrosliceDescriptor>(msd));
        }
    }

}

void Application::run() {
    uint64_t limit = par_.maximum_number();


    if (par_.create_dtsa()){
        int i = 0;
        uint64_t ts_index = 0;
        uint64_t ts_pos = 0;
        for (unsigned long j = 0; j < par_.num_ts(); j++){
            fles::TDescriptor TD = create_new_descriptor_ts(ts_index, ts_pos, par_.timeslice_size() - 1, i);
            i += par_.timeslice_size() - 1;
            sink->put(std::make_shared<fles::TDescriptor> (TD));
            ++count_;
        };
    }
    if (par_.dtsa2dmsa()){
        while(auto TD = source_descriptors->get()){
            std::shared_ptr<fles::TDescriptor> TD_S = (std::move(TD));
            dtsa2dmsa_writer(TD_S);
            ++count_;
        }
    }
    else{
        uint64_t index = 0;   
        for (auto source : sources_){
            auto sink = sinks_[index];
            L_(info) << "current file: "<<par_.input_archives()[index];
            while (auto ts = source->get()) {
                std::shared_ptr<fles::TDescriptor> TD = std::make_shared<fles::TDescriptor>(create_descriptor_ts(std::move(ts)));
                sink->put(TD);
                ++count_;
                
                if (count_ == limit) {
                    break;
                }
                // avoid unneccessary pipelining
                ts.reset();
            }
            index++;   
        }
    }
    for (auto& sink : sinks_){
        sink->end_stream();
    }


}
