// Copyright 2012-2013 Jan de Cuveland <cmail@cuveland.de>

#include "Application.hpp"
#include "ManagedTimesliceBuffer.hpp"
#include "StorableTimeslice.hpp"
#include "StorableTimesliceDescriptor.hpp"
#include "Timeslice.hpp"
#include "TDescriptor.hpp"
#include "TimesliceAnalyzer.hpp"
#include "TimesliceAutoSource.hpp"
#include "TimesliceDebugger.hpp"
#include "TimesliceOutputArchive.hpp"
#include "TimesliceDescriptorOutputArchive.hpp"
#include "TimeslicePublisher.hpp"
#include "Utility.hpp"
#include <cstdint>
#include <memory>
#include <thread>
#include <utility>

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

  source_ = std::make_unique<fles::TimesliceAutoSource>(par_.input_uri());

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
      sinks_.push_back(std::unique_ptr<fles::TimesliceSink>(
          new ManagedTimesliceBuffer(zmq_context_, shm_identifier, datasize,
                                     descsize, num_components)));
      has_shm_output = true;

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

/*
Anleitung zum Bauen dieses Tools.
Schritt 1: Definiere neue Klasse für Timeslice-Descriptoren kombiniert mit Microslice-Descriptoren
Schritt 2: Baue ein neues Archive .dtsa Dateien für Timeslice-Descriptoren
Schritt 3: Baue ein Tool, was .tsa Dateien in .dtsa Dateien umwandelt
Schritt 4: Erweitere tsclient, sodass auch .dtsa Dateien eingelesen werden können.
Schritt 5: Erweitere Tool aus Schritt 3, sodass .dtsa Dateien auch generiert werden können.
Schritt 6: Erweitere Tool aus Schritt 3, sodass .dtsa Dateien auch in .dmsa Dateien umgewandelt werden können.
*/
/*
void Application::create_microslices(uint8_t content_ptr, std::shared_ptr<fles::Timeslice> ts){
  size_t data_size = 1;
  long long acc_size = 0;
  for (uint64_t tsc = 0; tsc < ts->num_components(); tsc++) {
    for (uint64_t msc = 0; msc < (ts->num_core_microslices()) + 1; msc++){ //overlap berücksichtigen
      std::unique_ptr<fles::MicrosliceView> ms_ptr =
        std::make_unique<fles::MicrosliceView>(
            ts->get_microslice(tsc, msc));  //berücksichtige das dtsa datein keine microslices, sonder microslice descriptoren besitzen
      std::shared_ptr<fles::Microslice> ms = std::make_shared<fles::MicrosliceView>(ms_ptr, content_ptr); 
      acc_size += data_size;
      content_ptr += acc_size;
      //microslice zu timeslice hinzufügen.
    } 
  }

}
*/
fles::TDescriptor Application::create_descriptor_ts(std::shared_ptr<const fles::Timeslice> ts){
  //define TDescriptor
  //std::cout<<"test11"<<std::endl;
  //fles::TimesliceDescriptor TSDesc = ts->get_desc();
  uint64_t ts_index = ts->index();
  uint64_t ts_pos = ts->tpos();
  uint64_t ts_num_corems = ts->num_core_microslices();
  //std::cout<<"test12"<<std::endl;
  //fles::TDescriptor TD(TSDesc); //muss noch irgendwie den descriptor übernehmen 
  fles::TDescriptor TD(ts_index,ts_pos,ts_num_corems);
  //std::cout<<"test13"<<std::endl;
  for (uint64_t tsc = 0; tsc < ts->num_components(); tsc++){
    //std::cout<<"test14"<<std::endl;
    uint64_t num_ms = ts->num_microslices(tsc);
    //std::cout<<"test15"<<std::endl;
    TD.append_component(num_ms);
    //std::cout<<"test16"<<std::endl;
    //TD.addcomponent
    std::cout<<"test2"<<std::endl;
    std::cout<<(ts-> num_microslices(tsc))<<std::endl;
    for (uint64_t msc = 0; msc < (ts-> num_microslices(tsc)); msc++){
      //Add microslice
      //do something
      //std::cout<<"test17"<<std::endl;
      fles::MicrosliceDescriptor ms_desc= ts->descriptor(tsc,msc);
      std::cout<<"test1 "<<msc<<std::endl;
      //std::cout<<"test18"<<std::endl;
      TD.append_ms_desc(tsc, msc, ms_desc);
      //std::cout<<"test19"<<std::endl;
    }
  }
  //std::cout<<"test20"<<std::endl;
  //return TDescriptor
  return TD;

}

void Application::run() {
  time_begin_ = std::chrono::high_resolution_clock::now();

  if (benchmark_) {
    benchmark_->run();
    return;
  }

  uint64_t limit = par_.maximum_number();

  uint64_t index = 0;
  if (false){
    uint8_t* free_ptr = nullptr;
    free_ptr = static_cast<uint8_t*>(malloc(sizeof(uint8_t)*1000000));
    if (free_ptr == nullptr){
        std::cout<<"malloc call failed, probably insufficient mem"<<std::endl;
        throw std::bad_alloc();
    }
    for (size_t i = 0; i < 1000000; ++i) {
      free_ptr[i] = static_cast<uint8_t>(rand());
    }
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
      if (par_.create_descriptor_ts()){
        //std::cout<<"test"<<std::endl;
        std::shared_ptr<fles::TDescriptor> TD = std::make_shared<fles::TDescriptor>(create_descriptor_ts(ts));
        //std::cout<<"test1"<<std::endl;
        for (auto& sink : sinks_descriptor) {
          sink->put(TD);
        }
        //std::cout<<"test2"<<std::endl;
      }
      else{
        for (auto& sink : sinks_) {
          sink->put(ts);
        }
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
