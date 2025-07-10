
#include "Application.hpp"
#include "ManagedTimesliceBuffer.hpp"
#include "StorableTimeslice.hpp"
#include "StorableTimesliceDescriptor.hpp"
#include "TimesliceBuilder.hpp"
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
    std::cout<<"test"<<std::endl;
    if (!dirExists(par_.output_folder().c_str()) && par_.output_folder() != ""){
        if(par_.create_folder()){
            std::filesystem::create_directories(par_.output_folder());
        }
        else{
            throw std::ios_base::failure ("Folder do not exists. Use parameter create Folders to create them.");
        }
    }
    if (!par_.input_archives().empty()){
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
    //TODO: PatternGen einbinden. Leider nicht so leicht da timeslices groß werden können.
  


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
  //std::cout<<"et"<<std::endl;
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
        std::cout<<"test12"<<std::endl;

    }else{
        uint64_t index = 0;   
        for (auto source : sources_){
            auto sink = sinks_[index];
            L_(info) << "current file: "<<par_.input_archives()[index];
            while (auto ts = source->get()) {
                std::shared_ptr<fles::TDescriptor> TD = std::make_shared<fles::TDescriptor>(create_descriptor_ts(std::move(ts)));

                sink->put(TD);

                //std::cout<<"test2"<<std::endl;
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
