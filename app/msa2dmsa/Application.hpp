#include "Parameters.hpp"
#include "Sink.hpp"
#include "MicrosliceSource.hpp"
#include <vector>

class Application {
public:
  explicit Application(Parameters const& par);

  Application(const Application&) = delete;
  void operator=(const Application&) = delete;

  ~Application();

  void run();

private:
    Parameters const& par_;

    std::vector<std::shared_ptr<fles::MicrosliceSource>> sources_;
    std::vector<std::shared_ptr<fles::MicrosliceDescriptor>>generated_descriptors;
    std::vector<std::shared_ptr<fles::MicrosliceDescriptorSink>> sinks_;
    std::shared_ptr<fles::MicrosliceDescriptorSink> sink;
    int dirExists(const char *path);

    uint64_t count_ = 0;
}; 