#include "Application.hpp"
#include "MicrosliceInputArchive.hpp"
#include "MicrosliceDescribtorOutputArchive.hpp"
#include "MicrosliceReceiver.hpp"
#include "log.hpp"
#include "PatternGenerator.hpp"
#include <cstdint>
#include <memory>
#include <filesystem>
#include <sys/stat.h>
#include <sys/types.h>





Application::Application(Parameters const& par) : par_(par){

    std::vector<std::string> output_archives;
    std::string output_string;
    if (!dirExists(par_.output_folder.c_str()) && par_.output_folder != ""){
        if(par_.create_folder){
            std::filesystem::create_directories(par_.output_folder);
        }
        else{
            throw std::ios_base::failure ("Folder do not exists. Use parameter create Folders to create them.");
        }
    }
    if (!par_.input_archives.empty()){
        for (auto input_archive : par_.input_archives){
            sources_.push_back(std::make_shared<fles::MicrosliceInputArchive>(input_archive));
            output_string = std::filesystem::path(input_archive).filename().string();
            output_string.resize(output_string.find(".msa"));
            output_string = par_.output_folder +output_string + ".dmsa";
            output_archives.push_back(output_string);
        }
    }
    if (par_.create_dmsa){
        uint64_t offset = 0;
        for (uint64_t i = 0; i < par_.num_ms; i++){
            generated_descriptors.push_back(std::make_shared<fles::MicrosliceDescriptor>(
                static_cast<fles::MicrosliceDescriptor>(PatternGenerator(i,
                                                                        par_.content_size_min,
                                                                        par_.content_size_max,
                                                                        offset))
                )
            );
            offset += generated_descriptors[i]->size;
        
        }
    }

    if (!output_archives.empty()){
        for (auto output_archive : output_archives){
            sinks_.push_back(std::shared_ptr<fles::MicrosliceDescriptorSink>(
               new fles::MicrosliceDescriptorOutputArchive(output_archive)));
        }
    }
    else if (!par_.output_archive.empty()){
        std::string output_archive = par_.output_folder + par_.output_archive;
        sink = std::shared_ptr<fles::MicrosliceDescriptorSink>(
               new fles::MicrosliceDescriptorOutputArchive(output_archive));
    }

};

int Application::dirExists(const char *path){
    struct stat info;
    if(stat(path, &info) != 0){ return 0;}
    else if(info.st_mode & S_IFDIR){ return 1;}
    else{ return 0; }
}

Application::~Application(){
    L_(info) << "total microslices processed: "<<count_;
}

void Application::run() {

    if (par_.create_dmsa){
        std::cout<< typeid(sink).name()<<std::endl;
        for (auto ms_desc : generated_descriptors){
            sink->put(ms_desc);
            count_++;
        }
    }else{
    int i = 0;
        for(auto source_ : sources_){
            auto sink = sinks_[i];
            L_(info) << "current file: "<<par_.input_archives[i];
            while (auto microslice = source_->get()){
                std::shared_ptr<const fles::Microslice> ms(std::move(microslice));
                sink->put(std::make_shared<fles::MicrosliceDescriptor>(ms->desc()));
                ++count_;   
            }
            i++;

        }
    }
    for (auto& sink : sinks_){
        sink->end_stream();
    }
}