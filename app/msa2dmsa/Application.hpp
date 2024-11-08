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

    std::unique_ptr<fles::MicrosliceSource> source_;
    std::vector<std::unique_ptr<fles::MicrosliceDescriptorSink>> sinks_;

    uint64_t count_ = 0;
};