// Copyright 2012-2013 Jan de Cuveland <cmail@cuveland.de>
#pragma once

#include "Benchmark.hpp"
#include "Monitor.hpp"
#include "Parameters.hpp"
#include "Sink.hpp"
#include "TimesliceDescriptor.hpp"
#include "TimesliceSource.hpp"
#include "TimesliceDescriptorSource.hpp"
#include "TimesliceBuilder.hpp"
#include "log.hpp"
#include <chrono>
#include <csignal>
#include <memory>
#include <vector>
#include <zmq.hpp>

/// %Application base class.
class Application {
public:
  Application(Parameters const& par, volatile sig_atomic_t* signal_status);

  Application(const Application&) = delete;
  void operator=(const Application&) = delete;

  ~Application();

  void run();

private:
  Parameters const& par_;
  volatile sig_atomic_t* signal_status_;

  /// The application's monitoring object
  std::unique_ptr<cbm::Monitor> monitor_;

  /// The application's ZeroMQ context
  zmq::context_t zmq_context_{1};

  std::unique_ptr<fles::TimesliceSource> source_;
  std::unique_ptr<fles::TimesliceDescriptorSource> source_descriptors;
  std::vector<std::unique_ptr<fles::TimesliceSink>> sinks_;
  std::vector<std::unique_ptr<fles::TimesliceDescriptorSink>> sinks_descriptor;
  std::unique_ptr<Benchmark> benchmark_;

  uint64_t count_ = 0;

  logging::OstreamLog status_log_{status};
  logging::OstreamLog debug_log_{debug};
  std::string output_prefix_;

  std::chrono::high_resolution_clock::time_point time_begin_;
  uint64_t first_ts_start_time_{};

  void rate_limit_delay() const;
  void native_speed_delay(uint64_t ts_start_time);
  std::shared_ptr<fles::Timeslice> create_microslices(uint8_t*& content_ptr, uint8_t* original_ptr,std::shared_ptr<fles::TDescriptor> ts,std::chrono::time_point<std::chrono::steady_clock>& lastTrigger, uint64_t& total_data, long long& acc_size);
  fles::TDescriptor create_descriptor_ts(std::shared_ptr<const fles::Timeslice> ts);
  fles::TDescriptor create_new_descriptor_ts(uint64_t ts_index, uint64_t ts_pos,uint64_t ts_num_corems, int i);
};
