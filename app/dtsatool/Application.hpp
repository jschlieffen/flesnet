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
  std::unique_ptr<fles::TimesliceDescriptorSource> source_descriptors;
  std::vector<std::shared_ptr<fles::TimesliceDescriptorSink>> sinks_;
  std::shared_ptr<fles::TimesliceDescriptorSink> sink;

  std::string output_prefix_;
  std::map<std::string, std::unique_ptr<fles::Sink<fles::MicrosliceDescriptor>>> msaFiles;


  int dirExists(const char *path);
  fles::TDescriptor create_descriptor_ts(std::shared_ptr<const fles::Timeslice> ts);
  fles::TDescriptor create_new_descriptor_ts(uint64_t ts_index, uint64_t ts_pos,uint64_t ts_num_corems, int i);
  std::string constructArchiveName(const fles::Subsystem& sys_id, const uint16_t& eq_id);
  void dtsa2dmsa_writer(std::shared_ptr<fles::TDescriptor> TD);
  uint64_t count_ = 0;

};