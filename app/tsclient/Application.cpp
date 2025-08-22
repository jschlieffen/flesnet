// Copyright 2012-2013 Jan de Cuveland <cmail@cuveland.de>

#include "Application.hpp"
#include "ArchiveDescriptor.hpp"
#include "Benchmark.hpp"
#include "ManagedTimesliceBuffer.hpp"
#include "ManagedTDescriptorBuffer.hpp"
#include "Monitor.hpp"
#include "Parameters.hpp"
#include "Sink.hpp"                     // TimesliceSink
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
#include "log.hpp"
#include <chrono>
#include <csignal>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

Application::Application(Parameters const& par,
                         volatile sig_atomic_t* signal_status)
    : par_(par), signal_status_(signal_status) {
  // start up monitoring
  if (!par.monitor_uri().empty()) {
    monitor_ = std::make_unique<cbm::Monitor>(par_.monitor_uri());
  }

  if (par_.client_index() != -1) {
    output_prefix_ = std::to_string(par_.client_index()) + ": ";
  }

  if (par_.descriptor_source()){
    source_descriptors = std::make_unique<fles::TimesliceDescriptorAutoSource>(par_.input_uri());
  }
  else{
    source_ = std::make_unique<fles::TimesliceAutoSource>(par_.input_uri());  
  }
  

  if (par_.analyze()) {
    if (par_.histograms()) {
      sinks_.push_back(std::unique_ptr<fles::TimesliceSink>(
          new TimesliceAnalyzer(1000, status_log_.stream, output_prefix_,
                                &std::cout, monitor_.get())));
    } else {
      sinks_.push_back(std::unique_ptr<fles::TimesliceSink>(
          new TimesliceAnalyzer(1000, status_log_.stream, output_prefix_,
                                nullptr, monitor_.get())));
    }
  }

  if (par_.verbosity() > 0) {
    sinks_.push_back(std::unique_ptr<fles::TimesliceSink>(
        new TimesliceDumper(debug_log_.stream, par_.verbosity())));
  }

  bool has_shm_output = false;
  for (const auto& output_uri : par_.output_uris()) {
    // If output_uri has no full URI pattern, everything is in "uri.path"
    UriComponents uri{output_uri};

    if (uri.scheme == "file" || uri.scheme.empty()) {
      only_shm_outputschemes = false;
      size_t items = SIZE_MAX;
      size_t bytes = SIZE_MAX;
      fles::ArchiveCompression compression = fles::ArchiveCompression::None;
      for (auto& [key, value] : uri.query_components) {
        if (key == "items") {
          items = stoull(value);
        } else if (key == "bytes") {
          bytes = stoull(value);
        } else if (key == "c") {
          if (value == "none") {
            compression = fles::ArchiveCompression::None;
          } else if (value == "zstd") {
            compression = fles::ArchiveCompression::Zstd;
          } else {
            throw std::runtime_error(
                "invalid compression type for scheme file: " + value);
          }
        } else {
          throw std::runtime_error(
              "query parameter not implemented for scheme file: " + key);
        }
      }
      const auto file_path = uri.authority + uri.path;
      if (par_.create_descriptor_ts()){
        std::cout<<"test"<<std::endl;
        if (items == SIZE_MAX && bytes == SIZE_MAX) {
          sinks_descriptor.push_back(std::unique_ptr<fles::TimesliceDescriptorSink>(
              new fles::TimesliceDescriptorOutputArchive(file_path, compression)));
        } else {
          sinks_descriptor.push_back(std::unique_ptr<fles::TimesliceDescriptorSink>(
              new fles::TimesliceDescriptorOutputArchiveSequence(file_path, items, bytes,
                                                                    compression)));
        }
      }
      else{
        if (items == SIZE_MAX && bytes == SIZE_MAX) {
          sinks_.push_back(std::unique_ptr<fles::TimesliceSink>(
              new fles::TimesliceOutputArchive(file_path, compression)));
        } else {
          sinks_.push_back(std::unique_ptr<fles::TimesliceSink>(
              new fles::TimesliceOutputArchiveSequence(file_path, items, bytes,
                                                      compression)));
        }
      }
    } else if (uri.scheme == "tcp") {
      only_shm_outputschemes = false;
      uint32_t hwm = 1;
      for (auto& [key, value] : uri.query_components) {
        if (key == "hwm") {
          hwm = stou(value);
        } else {
          throw std::runtime_error(
              "query parameter not implemented for scheme " + uri.scheme +
              ": " + key);
        }
      }
      const auto address = uri.scheme + "://" + uri.authority;
      sinks_.push_back(std::unique_ptr<fles::TimesliceSink>(
          new fles::TimeslicePublisher(address, hwm)));

    } else if (uri.scheme == "shm") {
      uint32_t num_components = 1;
      uint32_t datasize = 27; // 128 MiB
      uint32_t descsize = 19; // 16 MiB
      for (auto& [key, value] : uri.query_components) {
        if (key == "datasize") {
          datasize = std::stoul(value);
        } else if (key == "descsize") {
          descsize = std::stoul(value);
        } else if (key == "n") {
          num_components = std::stoul(value);
        } else {
          throw std::runtime_error(
              "query parameter not implemented for scheme " + uri.scheme +
              ": " + key);
        }
      }
      const auto shm_identifier = split(uri.path, "/").at(0);
      if (par_.descriptor_source()){
      sinks_descriptor.push_back(std::unique_ptr<fles::TimesliceDescriptorSink>(
          new ManagedTDescriptorBuffer(zmq_context_, shm_identifier, datasize,
                                     descsize, num_components)));
      has_shm_output = true;
      }
      else{     
       sinks_.push_back(std::unique_ptr<fles::TimesliceSink>(
          new ManagedTimesliceBuffer(zmq_context_, shm_identifier, datasize,
                                     descsize, num_components)));
      has_shm_output = true;}
    } else {
      throw ParametersException("invalid output scheme: " + uri.scheme);
    }
  }

  if (has_shm_output) {
    // wait a moment to allow the ManagedTimesliceBuffer clients to connect
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
  }

  if (par_.benchmark()) {
    benchmark_ = std::make_unique<Benchmark>();
  }

  if (par_.rate_limit() != 0.0) {
    L_(info) << output_prefix_ << "rate limit active: "
             << human_readable_count(par_.rate_limit(), true, "Hz");
  }
}

Application::~Application() {
  L_(info) << output_prefix_ << "total timeslices processed: " << count_;

  // delay to allow monitor to process pending messages
  constexpr auto destruct_delay = std::chrono::milliseconds(200);
  std::this_thread::sleep_for(destruct_delay);
}

void Application::rate_limit_delay() const {
  auto delta_is = std::chrono::high_resolution_clock::now() - time_begin_;
  auto delta_want = std::chrono::microseconds(
      static_cast<uint64_t>(count_ * 1.0e6 / par_.rate_limit()));

  if (delta_want > delta_is) {
    std::this_thread::sleep_for(delta_want - delta_is);
  }
}

void Application::native_speed_delay(uint64_t ts_start_time) {
  if (count_ == 0) {
    first_ts_start_time_ = ts_start_time;
  } else {
    auto delta_is = std::chrono::high_resolution_clock::now() - time_begin_;
    auto delta_want =
        std::chrono::nanoseconds(ts_start_time - first_ts_start_time_) /
        par_.native_speed();
    if (delta_want > delta_is) {
      std::this_thread::sleep_for(delta_want - delta_is);
    }
  }
}



std::shared_ptr<fles::Timeslice> Application::create_microslices(uint8_t*& content_ptr,uint8_t* original_ptr, std::shared_ptr<fles::TDescriptor> ts,
                                                                long long& acc_size){
  size_t data_size = 1;

  uint64_t ts_index = ts->index();
  uint64_t ts_pos = ts->tpos(); //noch hinzufügen
  uint64_t ts_num_corems = ts->num_core_microslices();
  fles::TimesliceBuilder TSBuild(ts_num_corems, ts_index,ts_pos);
  for (uint64_t tsc = 0; tsc < ts->num_components(); tsc++) {
    uint64_t num_ms = ts->num_microslices(tsc);
    TSBuild.append_component(num_ms);
    for (uint64_t msc = 0; msc < (ts->num_core_microslices()) + 1; msc++){ //overlap berücksichtigen
      fles::MicrosliceDescriptor ms_desc = ts->descriptor(tsc, msc);  
      data_size = ms_desc.size;
      if (acc_size+data_size >= 1000000000){
        content_ptr = original_ptr;
        acc_size = 0;
      }
      std::shared_ptr<fles::Microslice> ms = std::make_shared<fles::MicrosliceView>(ms_desc, content_ptr);
      TSBuild.append_microslice(tsc,msc,*ms);
      acc_size += data_size;
      content_ptr += data_size;
    } 
  }
  auto timeslice = std::shared_ptr<fles::Timeslice>(std::make_shared<fles::TimesliceBuilder>(std::move(TSBuild))); 
  return std::static_pointer_cast<fles::Timeslice>(timeslice);
}

std::shared_ptr<fles::TDescriptor> Application::create_ms_cpointer(uint8_t*& content_ptr, uint8_t* original_ptr, 
                                                                  std::shared_ptr<fles::TDescriptor> ts, long long& acc_size){
  size_t data_size = 1;
  uint64_t ts_index = ts->index();
  uint64_t ts_pos = ts->tpos(); //noch hinzufügen
  uint64_t ts_num_corems = ts->num_core_microslices();
  fles::TDescriptor TSDescBuild(ts_num_corems, ts_index,ts_pos);
  //int64_t timeslice_size = 0;
  for (uint64_t tsc = 0; tsc < ts->num_components(); tsc++) {
    uint64_t num_ms = ts->num_microslices(tsc);
    TSDescBuild.append_component(num_ms);
    uint64_t size_component = (ts->num_microslices(tsc)*sizeof(fles::MicrosliceDescriptor));
    for (uint64_t msc = 0; msc < (ts->num_core_microslices()) + 1; msc++){ //overlap berücksichtigen
      fles::MicrosliceDescriptor ms_desc = ts->descriptor(tsc, msc);  
      data_size = ms_desc.size;
      if (acc_size+data_size >= par_.malloc_size()){
        content_ptr = original_ptr;
        acc_size = 0;
      }
      std::shared_ptr<fles::Microslice> ms = std::make_shared<fles::MicrosliceView>(ms_desc, content_ptr);
      TSDescBuild.append_microslice(tsc,msc,*ms);
      size_component += data_size;
      acc_size += data_size;
      if (par_.jump_val() == -1){
        content_ptr += data_size;
      } else {
        content_ptr += par_.jump_val();
      }
    TSDescBuild.set_size_component(tsc, size_component);
    } 
  }
  auto TSDesc = std::make_shared<fles::TDescriptor>(std::move(TSDescBuild)); 
  return std::static_pointer_cast<fles::TDescriptor>(TSDesc);
}

void Application::run() {
  time_begin_ = std::chrono::high_resolution_clock::now();

  if (benchmark_) {
    benchmark_->run();
    return;
  }

  uint64_t limit = par_.maximum_number();

  uint64_t index = 0;
  
  if (par_.descriptor_source()){
    uint8_t* free_ptr = nullptr;
    free_ptr = static_cast<uint8_t*>(malloc(sizeof(uint8_t)*par_.malloc_size()));
    if (free_ptr == nullptr){
        std::cout<<"malloc call failed, probably insufficient mem"<<std::endl;
        throw std::bad_alloc();
    }
    
    for (size_t i = 0; i < 1000000000; ++i) {
      free_ptr[i] = static_cast<uint8_t>(rand());
    }
    
    long long acc_size;
    //std::cout<<"test"<<std::endl;
    L_(info)<<"start";
    uint8_t* content_ptr = free_ptr;
    if (only_shm_outputschemes){
      std::vector<std::shared_ptr<const fles::TDescriptor>> test_vec;
      while (auto TDesc = source_descriptors->get()) {
        if (index >= par_.offset() &&
            (index - par_.offset()) % par_.stride() == 0) {
          ++index;
        } else {
          ++index;
          continue;
        }

        std::shared_ptr<fles::TDescriptor> timeslice = create_ms_cpointer(content_ptr, free_ptr, 
                                                                      std::move(TDesc), acc_size);
        std::shared_ptr<const fles::TDescriptor> ts;
        if (par_.release_mode()) {
          ts = std::make_shared<const fles::StorableTimesliceDescriptor>(*timeslice);
          timeslice.reset();
        } else {
          ts = std::shared_ptr<const fles::TDescriptor>(std::move(timeslice));
        }
        if (par_.native_speed() != 0.0) {
          native_speed_delay(ts->start_time());
        }
        if (par_.rate_limit() != 0.0) {
          rate_limit_delay();
        }
        
        if (count_ == limit || *signal_status_ != 0) {
          break;
        }
        // avoid unneccessary pipelining
        timeslice.reset();
        test_vec.push_back(ts);
      }
      std::cout<<"test123"<<std::endl;
      auto t1 = std::chrono::high_resolution_clock::now();
      for (std::shared_ptr<const fles::TDescriptor> ts : test_vec){
        for (auto& sink : sinks_descriptor){
          sink->put(ts);
        ts.reset();
        ++count_;
        }
      }
      auto t2 = std::chrono::high_resolution_clock::now();
      auto duration = std::chrono::duration_cast<std::chrono::seconds>(t2 - t1).count();
      L_(info) << "Time needed: "<< duration;

      

    } else {
      while (auto TDesc = source_descriptors->get()) {

        if (index >= par_.offset() &&
            (index - par_.offset()) % par_.stride() == 0) {
          ++index;
        } else {
          ++index;
          continue;
        }
        std::shared_ptr<const fles::Timeslice> timeslice = (create_microslices(content_ptr, free_ptr, std::move(TDesc), acc_size));
        std::shared_ptr<const fles::Timeslice> ts;
        if (par_.release_mode()) {
          ts = std::make_shared<const fles::StorableTimeslice>(*timeslice);
          timeslice.reset();
        } else {
          ts = std::shared_ptr<const fles::Timeslice>(std::move(timeslice));
        }
        if (par_.native_speed() != 0.0) {
          native_speed_delay(ts->start_time());
        }
        if (par_.rate_limit() != 0.0) {
          rate_limit_delay();
        }
        ++count_;
        if (count_ == limit || *signal_status_ != 0) {
          break;
        }
        // avoid unneccessary pipelining
        timeslice.reset();
      
        for (auto& sink : sinks_){
          sink->put(ts);
        ts.reset();
        }
      }
    }
    free(free_ptr);
  }
  else{    
    while (auto timeslice = source_->get()) {
      if (index >= par_.offset() &&
          (index - par_.offset()) % par_.stride() == 0) {
        ++index;
      } else {
        ++index;
        continue;
      }
      std::shared_ptr<const fles::Timeslice> ts;
      if (par_.release_mode()) {
        ts = std::make_shared<const fles::StorableTimeslice>(*timeslice);
        timeslice.reset();
      } else {
        ts = std::shared_ptr<const fles::Timeslice>(std::move(timeslice));
      }
      if (par_.native_speed() != 0.0) {
        native_speed_delay(ts->start_time());
      }
      if (par_.rate_limit() != 0.0) {
        rate_limit_delay();
      }

      for (auto& sink : sinks_) {
        sink->put(ts);
      }

      ++count_;
      if (count_ == limit || *signal_status_ != 0) {
        break;
      }
      // avoid unneccessary pipelining
      timeslice.reset();
    }
  }
  // Loop over sinks. For all sinks of type ManagedTimesliceBuffer, check if
  // they are empty. If at least one of them is not empty, wait for 100 ms.
  // Repeat until all sinks are empty.
  bool all_empty = false;
  bool first = true;
  *signal_status_ = 0;
  while (!all_empty && *signal_status_ == 0) {
    all_empty = true;
    for (auto& sink : sinks_) {
      auto* mtb = dynamic_cast<ManagedTimesliceBuffer*>(sink.get());
      if (mtb != nullptr) {
        mtb->handle_timeslice_completions();
        if (!mtb->empty()) {
          all_empty = false;
          if (first) {
            L_(info) << output_prefix_ << "waiting for shm buffer to empty";
            L_(info) << output_prefix_ << "press Ctrl-C to abort";
            first = false;
          }
          std::this_thread::sleep_for(std::chrono::milliseconds(100));
          break;
        }
      }
    }
  }
}
