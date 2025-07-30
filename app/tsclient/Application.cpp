// Copyright 2012-2013 Jan de Cuveland <cmail@cuveland.de>

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
#include <chrono>
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

//Remains: InputArchive für TDescriptoren erstellen, main iteration anpassen. Malloc Größe anpassen.
/* TODO: Die Lauzeit von dieser Funktion ist recht schlecht. Das liegt daran,
 dass Timeslices die Daten nochmal abspeichern. Ich muss also eine Klasse erzeugen,
 welche lediglich den Pointer abspeichert und nicht die Daten selber und erst bei der 
 put Funktion die Daten ausliest und abspeichert.
 Die TDescriptoren dürfen nicht in einen Timeslice umgewandelt werden, da ansonsten es zu kompliziert
 den Pointer auszulesen. Stattdessen lieber eine neue Klasse definieren, welche shared_ptr von Microslices 
 einliest. Darüber kann man dann die Microslices leichter einzelnen behandeln.
*/

std::shared_ptr<fles::Timeslice> Application::create_microslices(uint8_t*& content_ptr,uint8_t* original_ptr, std::shared_ptr<fles::TDescriptor> ts,
std::chrono::time_point<std::chrono::steady_clock>& lastTrigger, uint64_t& total_data, long long& acc_size){
  size_t data_size = 1;

  uint64_t ts_index = ts->index();
  uint64_t ts_pos = ts->tpos(); //noch hinzufügen
  uint64_t ts_num_corems = ts->num_core_microslices();
  fles::TimesliceBuilder TSBuild(ts_num_corems, ts_index,ts_pos);
  for (uint64_t tsc = 0; tsc < ts->num_components(); tsc++) {
    uint64_t num_ms = ts->num_microslices(tsc);
    TSBuild.append_component(num_ms);
    for (uint64_t msc = 0; msc < (ts->num_core_microslices()) + 1; msc++){ //overlap berücksichtigen

      //std::shared_ptr<fles::MicrosliceView> ms_ptr =
        //std::make_shared<fles::MicrosliceView>(
          //  ts->descriptor(tsc, msc), content_ptr);  //berücksichtige das dtsa datein keine microslices, sonder microslice descriptoren besitzen
      fles::MicrosliceDescriptor ms_desc = ts->descriptor(tsc, msc);  
      data_size = ms_desc.size;
      //std::cout<<data_size<<std::endl;
      //std::cout<<acc_size+data_size<<std::endl;
      if (acc_size+data_size >= 1000000000){
        //std::cout<<"test1233"<<std::endl;
        content_ptr = original_ptr;
        acc_size = 0;
      }

      std::shared_ptr<fles::Microslice> ms = std::make_shared<fles::MicrosliceView>(ms_desc, content_ptr);
      TSBuild.append_microslice(tsc,msc,*ms);
      acc_size += data_size;
      //acc_size += 10000;
      content_ptr += data_size;
      //std::cout<<"test1"<<std::endl;
      //std::cout<<acc_size<<std::endl;

      auto now = std::chrono::steady_clock::now();
      auto elapsed = std::chrono::duration_cast<std::chrono::seconds>(now - lastTrigger);
      if (elapsed.count() >= 1) {
            // One second (or more) has passed
            total_data += data_size;
             double gb = static_cast<double>(total_data) / (1024 * 1024 * 1024);
            std::cout << std::fixed << std::setprecision(2);
            std::cout << "Data in GB/s: "<<gb <<std::endl;
            // Update last trigger time
            total_data = 0;
            lastTrigger = now;
        } 
      else{
        total_data += data_size;
      }

      //foobar
      //microslice zu timeslice hinzufügen.
    } 
    //return std::make_shared<fles::TimesliceBuilder>(std::move(TSBuild));

  }
  auto timeslice = std::shared_ptr<fles::Timeslice>(std::make_shared<fles::TimesliceBuilder>(std::move(TSBuild))); 
  return std::static_pointer_cast<fles::Timeslice>(timeslice);

}

fles::TDescriptor Application::create_descriptor_ts(std::shared_ptr<const fles::Timeslice> ts){
  //define TDescriptor
  //std::cout<<"test11"<<std::endl;
  //fles::TimesliceDescriptor TSDesc = ts->get_desc();
  uint64_t ts_index = ts->index();
  uint64_t ts_pos = ts->tpos();
  uint64_t ts_num_corems = ts->num_core_microslices();
  //std::cout<<"test12"<<std::endl;
  //fles::TDescriptor TD(TSDesc); //muss noch irgendwie den descriptor übernehmen 
  fles::TDescriptor TD(ts_num_corems, ts_index,ts_pos);
  //std::cout<<"test13"<<std::endl;
  for (uint64_t tsc = 0; tsc < ts->num_components(); tsc++){
    //std::cout<<"test14"<<std::endl;
    uint64_t num_ms = ts->num_microslices(tsc);
    //std::cout<<"test15"<<std::endl;
    TD.append_component(num_ms);
    //std::cout<<"test16"<<std::endl;
    //TD.addcomponent
    //std::cout<<"test2"<<std::endl;
    //std::cout<<(ts-> num_microslices(tsc))<<std::endl;
    for (uint64_t msc = 0; msc < (ts-> num_microslices(tsc)); msc++){
      //Add microslice
      //do something
      //std::cout<<"test17"<<std::endl;
      fles::MicrosliceDescriptor ms_desc= ts->descriptor(tsc,msc);
      //std::cout<<"test1 "<<msc<<std::endl;
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
  
  if (par_.descriptor_source()){
    std::vector<std::shared_ptr<const fles::Timeslice>> test_vec;
    uint8_t* free_ptr = nullptr;
    free_ptr = static_cast<uint8_t*>(malloc(sizeof(uint8_t)*1000000000));
    if (free_ptr == nullptr){
        std::cout<<"malloc call failed, probably insufficient mem"<<std::endl;
        throw std::bad_alloc();
    }
    for (size_t i = 0; i < 1000000000; ++i) {
      free_ptr[i] = static_cast<uint8_t>(rand());
    }
    long long acc_size;
    std::cout<<"test"<<std::endl;
    uint8_t* content_ptr = free_ptr;
    auto lastTrigger = std::chrono::steady_clock::now();
    uint64_t total_data = 0;
    while (auto TDesc = source_descriptors->get()) {
      auto t1_big = std::chrono::steady_clock::now(); 
      if (index >= par_.offset() &&
          (index - par_.offset()) % par_.stride() == 0) {
        ++index;
      } else {
        ++index;
        continue;
      }
      auto t1 = std::chrono::steady_clock::now(); 
      std::shared_ptr<const fles::Timeslice> timeslice = (create_microslices(content_ptr, free_ptr, std::move(TDesc), lastTrigger, total_data, acc_size));
      auto t2 = std::chrono::steady_clock::now();
      auto duration_us = std::chrono::duration_cast<std::chrono::microseconds>(t2 - t1).count();
      //std::cout<<duration_us<<std::endl;
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
      //for (auto& sink : sinks_) {
        //sink->put(ts);
      //}
      test_vec.push_back(ts);
      ++count_;
      if (count_ == limit || *signal_status_ != 0) {
        break;
      }
      // avoid unneccessary pipelining
      timeslice.reset();
      auto t2_big = std::chrono::steady_clock::now(); 
      auto duration_us_big = std::chrono::duration_cast<std::chrono::microseconds>(t2_big - t1_big).count();
      //std::cout<<"whole loop "<<duration_us_big<<std::endl;
    }
    for (std::shared_ptr<const fles::Timeslice> ts : test_vec){
      for (auto& sink : sinks_){
        sink->put(ts);
      }
      ts.reset();
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
