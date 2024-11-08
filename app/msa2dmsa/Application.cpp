#include "Application.hpp"
#include "MicrosliceInputArchive.hpp"
#include "MicrosliceDescribtorOutputArchive.hpp"
#include "MicrosliceReceiver.hpp"
#include "log.hpp"
#include <memory>


Application::Application(Parameters const& par) : par_(par){

    if (!par_.input_archive.empty()){
        source_ =
            std::make_unique<fles::MicrosliceInputArchive>(par_.input_archive);
    }

    if (!par_.output_archive.empty()){
        sinks_.push_back(std::unique_ptr<fles::MicrosliceDescriptorSink>(
            new fles::MicrosliceDescriptorOutputArchive(par_.output_archive)));
    }

};

Application::~Application(){
    L_(info) << "total microslices processed: "<<count_;
}

void Application::run() {

    while (auto microslice = source_->get()){
        std::shared_ptr<const fles::Microslice> ms(std::move(microslice));
        for (auto& sink : sinks_){
            sink->put(std::make_shared<fles::MicrosliceDescriptor>(ms->desc()));
        }
        ++count_;   
    }
    for (auto& sink : sinks_){
        sink->end_stream();
    }
}