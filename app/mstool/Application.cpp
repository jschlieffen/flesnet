// Copyright 2012-2015 Jan de Cuveland <cmail@cuveland.de>

#include "Application.hpp"
#include "FlesnetPatternGenerator.hpp"
#include "MicrosliceAnalyzer.hpp"
#include "MicrosliceInputArchive.hpp"
#include "MicrosliceOutputArchive.hpp"
#include "MicrosliceReceiver.hpp"
#include "MicrosliceTransmitter.hpp"
#include "TimesliceDebugger.hpp"
#include "log.hpp"
#include "shm_channel_client.hpp"
#include <chrono>
#include <iostream>
#include <memory>
#include <thread>


Application::Application(Parameters const& par) : par_(par) {

  // Source setup
  if (!par_.input_shm.empty()) {
    L_(info) << "using shared memory as data source: " << par_.input_shm;

    shm_device_ = std::make_shared<flib_shm_device_client>(par_.input_shm);

    if (par_.channel_idx < shm_device_->num_channels()) {
      data_source_ = std::make_unique<flib_shm_channel_client>(
          shm_device_, par_.channel_idx);

    } else {
      throw std::runtime_error("shared memory channel not available");
    }
  } else if (par_.use_pattern_generator) {
    L_(info) << "using pattern generator as data source";

    uint32_t typical_content_size = par_.content_size;
    constexpr std::size_t desc_buffer_size_exp = 19; // 512 ki entries
    constexpr std::size_t data_buffer_size_exp = 27; // 128 MiB

    data_source_ = std::make_unique<FlesnetPatternGenerator>(
        data_buffer_size_exp, desc_buffer_size_exp, par_.channel_idx,
        typical_content_size, true, true);
  }

  if (data_source_) {
    source_ = std::make_unique<fles::MicrosliceReceiver>(*data_source_);
  } else if (!par_.input_archive.empty()&&!par_.descriptor_source) {
    source_ =
        std::make_unique<fles::MicrosliceInputArchive>(par_.input_archive);
  }
  else if (!par_.input_archive.empty()&&par_.descriptor_source){
    source_descriptors =
        std::make_unique<fles::MicrosliceDescriptorInputArchive>(par_.input_archive);
  }
  

  // Sink setup
  if (par_.analyze) {
    sinks_.push_back(std::unique_ptr<fles::MicrosliceSink>(
        new MicrosliceAnalyzer(100000, 3, std::cout, "", par_.channel_idx)));
  }

  if (par_.dump_verbosity > 0) {
    sinks_.push_back(std::unique_ptr<fles::MicrosliceSink>(
        new MicrosliceDumper(std::cout, par_.dump_verbosity)));
  }

  if (!par_.output_archive.empty()) {
    sinks_.push_back(std::unique_ptr<fles::MicrosliceSink>(
        new fles::MicrosliceOutputArchive(par_.output_archive)));
  }

  if (!par_.output_shm.empty()) {
    L_(info) << "providing output in shared memory: " << par_.output_shm;

    constexpr std::size_t desc_buffer_size_exp = 19; // 512 ki entries
    constexpr std::size_t data_buffer_size_exp = 27; // 128 MiB

    output_shm_device_ = std::make_unique<flib_shm_device_provider>(
        par_.output_shm, 1, data_buffer_size_exp, desc_buffer_size_exp);
    InputBufferWriteInterface* data_sink = output_shm_device_->channels().at(0);
    sinks_.push_back(std::unique_ptr<fles::MicrosliceSink>(
        new fles::MicrosliceTransmitter(*data_sink)));
  }
}

Application::~Application() {
  L_(info) << "total microslices processed: " << count_;
}

uint64_t to_uint64_t(long long value) { 
    assert(value >= 0); 
    return static_cast<uint64_t>(value); 
}

void flush_cache() {
    static std::vector<char> dummy(64 * 1024 * 1024, 1); // 64MB
    for (size_t i = 0; i < dummy.size(); i += 64) {
        dummy[i]++;
    }
}

void Application::run() {
   uint64_t limit = par_.maximum_number;
  const auto t1 = std::chrono::high_resolution_clock::now();
  uint64_t current_index = 0;
  uint64_t last_index = 0;
  uint8_t* free_ptr = nullptr;
  long long acc_size = 0; 
  std::vector<std::shared_ptr<const fles::Microslice>> test_vec;
  if (par_.descriptor_source){
    free_ptr = static_cast<uint8_t*>(malloc(sizeof(uint8_t)*par_.malloc_size));


    if (free_ptr == nullptr){
      std::cout<<"malloc call failed, probably insufficient mem"<<std::endl;
      throw std::bad_alloc();
    }
    for (size_t i = 0; i < par_.malloc_size; ++i) {
      free_ptr[i] = static_cast<uint8_t>(rand());
    }
      std::cout<<free_ptr <<std::endl;
    while (auto microslicedescriptor = source_descriptors->get()) {
      std::shared_ptr<const fles::MicrosliceDescriptor> ms_desc(std::move(microslicedescriptor));
      current_index = ms_desc->idx;
      /*
      //Florian oder Nico fragen, ob das noch so bestehen soll.
      const auto t2 = std::chrono::high_resolution_clock::now();
      const auto current_time_long = std::chrono::duration_cast<std::chrono::nanoseconds>(t2 - t1);
      uint64_t current_time = to_uint64_t(current_time_long.count());
      while (current_index - last_index > current_time){
        const auto t2 = std::chrono::high_resolution_clock::now();
        const auto current_time_long = std::chrono::duration_cast<std::chrono::nanoseconds>(t2 - t1);
        current_time = to_uint64_t(current_time_long.count());
      }
      */
      fles::MicrosliceDescriptor desc_ = *ms_desc.get();

      long data_size = desc_.size;
      if (par_.malloc_size<=desc_.size){
        throw std::invalid_argument("malloc call is smaller than size of ms");
      }        
      if (acc_size + data_size >= par_.malloc_size) {
        acc_size = 0;
      }

      uint8_t* content_ptr = free_ptr + acc_size;


      std::shared_ptr<fles::Microslice> ms = std::make_shared<fles::MicrosliceView>(desc_, content_ptr); 

      test_vec.push_back(ms);
      if (par_.jump_val == -1){
        acc_size += data_size;
      }
      else{
        acc_size += par_.jump_val;
      }
      
      ++count_;
      if (count_ == limit) {
        break;
      }
      
    }
    for (std::shared_ptr<const fles::Microslice> ms : test_vec){
      for (auto& sink : sinks_) {
        sink->put(ms);
      }
    }
    for (auto& sink : sinks_) {
      sink->end_stream();
    }
    free(free_ptr);
  }
  else{
    while (auto microslice = source_->get()) {
      std::shared_ptr<const fles::Microslice> ms(std::move(microslice));
      last_index = current_index;
      current_index = ms->desc().idx;
      if (last_index == 0){
          last_index = current_index;
      }
      const auto t2 = std::chrono::high_resolution_clock::now();
      const auto current_time_long = std::chrono::duration_cast<std::chrono::nanoseconds>(t2 - t1);
      uint64_t current_time = to_uint64_t(current_time_long.count());
      while (current_index - last_index > current_time){
          const auto t2 = std::chrono::high_resolution_clock::now();
          const auto current_time_long = std::chrono::duration_cast<std::chrono::nanoseconds>(t2 - t1);
          current_time = to_uint64_t(current_time_long.count());
      }
        for (auto& sink : sinks_) {
          sink->put(ms);
        } 
      ++count_;
      if (count_ == limit) {
        break;
      }
      
    }
    for (auto& sink : sinks_) {
      sink->end_stream();
    }
  }
  if (output_shm_device_) {
    L_(info) << "waiting until output shared memory is empty";
    while (!output_shm_device_->channels().at(0)->empty()) {
      std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
  }

}
