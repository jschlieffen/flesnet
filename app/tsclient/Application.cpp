// Copyright 2012-2013 Jan de Cuveland <cmail@cuveland.de>

#include "Application.hpp"
#include "ArchiveDescriptor.hpp"
#include "Benchmark.hpp"
#include "Monitor.hpp"
#include "OptionValues.hpp"
#include "Parameters.hpp"
#include "Sink.hpp" // TimesliceSink
#include "StorableTimeslice.hpp"
#include "StorableTimesliceDescriptor.hpp"
#include "TimesliceBuilder.hpp"
#include "Timeslice.hpp"
#include "TDescriptor.hpp"
#include "TimesliceAnalyzer.hpp"
#include "TimesliceSource.hpp"
#include "TimesliceAutoSource.hpp"
#include "TimesliceDescriptorAutoSource.hpp"
#include "TimesliceDebugger.hpp"
#include "TimesliceOutputArchive.hpp"
#include "TimesliceDescriptorOutputArchive.hpp"
#include "TimeslicePublisher.hpp"
#include "TimesliceShmSink.hpp"
#include "TDescriptorShmSink.hpp"
#include "Utility.hpp"
#include "log_short.hpp"
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
      if (monitor_) {
        // The callback runs on the source's communication thread, which is why it
        // reports a connection loss even while the main loop is blocked in get().
        const std::string prefix = output_prefix_.empty() ? ":" : output_prefix_;
        source_descriptors->set_state_callback(
            [this, prefix](ConnectionState state, const std::string& reason) {
              monitor_->QueueMetric(
                  "timeslice_source_status",
                  {{"host", monitor_->HostName()}, {"output_prefix", prefix}},
                  {{"state", to_string(state)}, {"reason", reason}});
            });
      }
    }
  else{
    source_ = std::make_unique<fles::TimesliceAutoSource>(par_.input_uri());  
    if (monitor_) {
      // The callback runs on the source's communication thread, which is why it
      // reports a connection loss even while the main loop is blocked in get().
      const std::string prefix = output_prefix_.empty() ? ":" : output_prefix_;
      source_->set_state_callback(
          [this, prefix](ConnectionState state, const std::string& reason) {
            monitor_->QueueMetric(
                "timeslice_source_status",
                {{"host", monitor_->HostName()}, {"output_prefix", prefix}},
                {{"state", to_string(state)}, {"reason", reason}});
          });
    }
  }
  



  if (par_.analyze()) {
    if (par_.histograms()) {
      sinks_.push_back(
          std::unique_ptr<fles::TimesliceSink>(new TimesliceAnalyzer(
              1000, output_prefix_, &std::cout, monitor_.get())));
    } else {
      sinks_.push_back(
          std::unique_ptr<fles::TimesliceSink>(new TimesliceAnalyzer(
              1000, output_prefix_, nullptr, monitor_.get())));
    }
  }

  if (par_.verbosity() > 0) {
    sinks_.push_back(std::unique_ptr<fles::TimesliceSink>(
        new TimesliceDumper(par_.verbosity())));
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
      std::size_t size = UINT64_C(1) << 30; // 1 GiB
      for (auto& [key, value] : uri.query_components) {
        if (key == "size") {
          size = fles::SizeValue::parse(value);
        } else if (key == "datasize" || key == "descsize" || key == "n") {
          throw std::runtime_error("query parameter no longer supported for "
                                   "scheme shm: " +
                                   key + " (use size instead, e.g. size=4GiB)");
        } else {
          throw std::runtime_error(
              "query parameter not implemented for scheme " + uri.scheme +
              ": " + key);
        }
      }
      const auto shm_identifier = split(uri.path, "/").at(0);
      if (par_.descriptor_source()){
      sinks_descriptor.push_back(std::make_unique<fles::TDescriptorShmSink>(
              zmq_context_, shm_identifier, size));
      has_shm_output = true;
      }
      else{     
          sinks_.push_back(std::make_unique<fles::TimesliceShmSink>(
              zmq_context_, shm_identifier, size));
      has_shm_output = true;}
    } else {
      throw ParametersException("invalid output scheme: " + uri.scheme);
    }
  }

  if (has_shm_output) {
    // wait a moment to allow the shared memory clients to connect
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
  }

  if (par_.benchmark()) {
    benchmark_ = std::make_unique<Benchmark>();
  }

  if (par_.rate_limit() != 0.0) {
    INFO("rate limit active: {} Hz", par_.rate_limit());
  }
}

Application::~Application() {
  INFO("total timeslices processed: {}", count_);

  // delay to allow monitor to process pending messages
  constexpr auto destruct_delay = std::chrono::milliseconds(200);
  std::this_thread::sleep_for(destruct_delay);
}

void Application::rate_limit_delay() const {
  if (count_ == 0) {
    return;
  }
  auto delta_is = std::chrono::high_resolution_clock::now() - time_begin_;
  auto delta_want = std::chrono::microseconds(
      static_cast<uint64_t>(count_ * 1.0e6 / par_.rate_limit()));
  try_delay(delta_want - delta_is);
}

void Application::native_speed_delay(uint64_t ts_start_time) {
  if (count_ == 0) {
    first_ts_start_time_ = ts_start_time;
  } else {
    auto delta_is = std::chrono::high_resolution_clock::now() - time_begin_;
    auto delta_want = std::chrono::nanoseconds(static_cast<uint64_t>(
        (ts_start_time - first_ts_start_time_) / par_.native_speed()));
    try_delay(delta_want - delta_is);
  }
}

void Application::try_delay(std::chrono::nanoseconds sleep_duration) const {
  if (sleep_duration.count() > 0) {
    DEBUG("maintaining replay rate, sleeping for {} s",
          std::chrono::duration_cast<std::chrono::milliseconds>(sleep_duration)
                  .count() /
              1000.);
    std::this_thread::sleep_for(sleep_duration);
  } else {
    WARN("replay rate not maintained, lacking by {} s",
         std::chrono::duration_cast<std::chrono::milliseconds>(sleep_duration)
                 .count() /
             1000.);
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
    for (uint64_t msc = 0; msc < (ts->num_core_microslices()); msc++){ //overlap berücksichtigen
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
    for (uint64_t msc = 0; msc < (ts->num_core_microslices()); msc++){ //overlap berücksichtigen
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
        //timeslice.reset();

        for (auto& sink : sinks_){
          sink->put(ts);
        ts.reset();
        }
      }
    }
    for (auto& sink : sinks_descriptor) {
      sink->end_stream();
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
    for (auto& sink : sinks_) {
      sink->end_stream();
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
      auto* shm_sink = dynamic_cast<fles::TimesliceShmSink*>(sink.get());
      if (shm_sink != nullptr) {
        shm_sink->handle_completions();
        if (!shm_sink->empty()) {
          all_empty = false;
          if (first) {
            INFO("waiting for shm buffer to empty");
            INFO("press Ctrl-C to abort");
            first = false;
          }
          std::this_thread::sleep_for(std::chrono::milliseconds(100));
          break;
        }
      }
    }
  }
}
