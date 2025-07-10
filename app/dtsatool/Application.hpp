#include "Parameters.hpp"
#include "Sink.hpp"
#include "TimesliceSource.hpp"
#include "TimesliceDescriptorSource.hpp"
#include <vector>

class Application {
public:
  Application(Parameters const& par);

  Application(const Application&) = delete;
  void operator=(const Application&) = delete;

  ~Application();

  void run();
private:

    Parameters const& par_;

  std::vector<std::shared_ptr<fles::TimesliceSource>> sources_;
  std::vector<std::shared_ptr<fles::MicrosliceDescriptor>>generated_descriptors;
  std::vector<std::shared_ptr<fles::TimesliceDescriptorSink>> sinks_;
  std::shared_ptr<fles::TimesliceDescriptorSink> sink;

  std::string output_prefix_;
  int dirExists(const char *path);
  fles::TDescriptor create_descriptor_ts(std::shared_ptr<const fles::Timeslice> ts);
fles::TDescriptor create_new_descriptor_ts(uint64_t ts_index, uint64_t ts_pos,uint64_t ts_num_corems, int i);

  uint64_t count_ = 0;

};