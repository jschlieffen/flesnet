#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#Created on Fri Apr 25 15:41:42 2025

#@author: jschlieffen

"""
Usage: 
    execution.py <flesctrl_logfile> [--verbose] [--mode=<mode>...]
    
Options:
    <flesctrl_logfile>  The general logfile of the flesctrl
    --verbose           flag for verbose mode [default: False]
    --mode=<mode>...       The mode for the execution (deserialization/plots etc.) [default: all]
"""



import Logfile_reader as LR
import Logfile_handler as LH
import plots 
import re
import docopt
import os
import sys

class execution:
    
    def __init__(self,flesctl_logfile):
        self.entry_nodes = []
        self.build_nodes = []
        self.flesctl_logfile = flesctl_logfile
        if not (os.path.isfile(flesctl_logfile)):
            print('file does not exist')
        self.get_node_names(flesctl_logfile)
        self.data_rates_entry_nodes = {}
        self.shm_usages_entry_nodes = {}
        self.data_rates_build_nodes = {}
        self.shm_usages_build_nodes = {}
        
    def get_node_names(self,flesctl_logfile_path):
        with open(flesctl_logfile_path, "r") as file:
            flesctl_logfile = file.read()
        pattern = re.compile(r"([a-zA-Z0-9-]+)\s+as\s+index\s+(\d+)")
        nodes_info = []
        node_types = ['Entry', 'Build']
        for node_type in node_types:
            matches = re.findall(f'{node_type} nodes:([\s\S]*?)(?=\n[A-Za-z]|$)', flesctl_logfile)
            if matches:
                for match in matches:
                    for name, index in re.findall(pattern, match):
                        nodes_info.append({'node_name': name, 'node_type': node_type, 'index': int(index)})
        for node in nodes_info:
            if node['node_type'] == 'Entry':
                self.entry_nodes.append((node['node_name'], node['index']))
            elif node['node_type'] == 'Build':
                self.build_nodes.append((node['node_name'], node['index']))

    def get_data_from_logfile(self):
        for entry_node in self.entry_nodes:
            Logfile_reader_cls = LR.Logfile_reader_entry_node(f"../logs/flesnet/entry_nodes/entry_node_{entry_node[0]}.log")
            Logfile_reader_cls.extract_data_rates()
            Logfile_reader_cls.extract_data_shms_entry_node()
            self.data_rates_entry_nodes[f"entry_node_{entry_node[0]}"] = Logfile_reader_cls.data_rate
            self.shm_usages_entry_nodes[f"entry_node_{entry_node[0]}"] = Logfile_reader_cls.data_shms
        for build_node in self.build_nodes:
            Logfile_reader_cls = LR.Logfile_reader_build_node(f"../logs/flesnet/build_nodes/build_node_{build_node[0]}.log")
            Logfile_reader_cls.extract_data_rates()
            Logfile_reader_cls.extract_data_shms_build_node()
            self.data_rates_build_nodes[f"build_node_{build_node[0]}"] = Logfile_reader_cls.data_rate
            self.shm_usages_build_nodes[f"build_node_{build_node[0]}"] = Logfile_reader_cls.data_shms

    #def get_data_from_deserialzation(self):
        
        
    def serialize_data_rates(self):
        Logfile_serializer_entry_nodes = LH.serialize_data("e",self.data_rates_entry_nodes, self.shm_usages_entry_nodes, self.flesctl_logfile)
        Logfile_serializer_entry_nodes.serialize_data_rates()
        Logfile_serializer_entry_nodes.serialize_shm_usage_entry_nodes()
        Logfile_serializer_build_nodes = LH.serialize_data("b", self.data_rates_build_nodes, self.shm_usages_build_nodes, self.flesctl_logfile)
        Logfile_serializer_build_nodes.serialize_data_rates()
        Logfile_serializer_build_nodes.serialize_shm_usage_build_nodes()

    def start_plots_entry_nodes(self):

        cp_cls = plots.create_plots_entry_nodes(self.data_rates_entry_nodes, self.shm_usages_entry_nodes)
        cp_cls.plot_total_data_rate()
        cp_cls.plot_avg_data_rate()
        cp_cls.plot_data_rate_single()
        cp_cls.plot_shm_usage()
        cp_cls.plot_shm_usage_single()

    def start_plots_build_nodes(self):
        cp_cls = plots.create_plots_build_nodes(self.data_rates_build_nodes, self.shm_usages_build_nodes)
        cp_cls.plot_total_data_rate()
        cp_cls.plot_avg_data_rate()
        cp_cls.plot_data_rate_single()
        cp_cls.plot_shm_usage_assemble()
        cp_cls.plot_shm_usage_single_node_avg()
        cp_cls.plot_shm_usage_single_node_single_entry_node()

def main():
    
    #exec_cls = execution("../logs/general/Run_13_2025-04-25-15-28-00.log")
    #exec_cls.start_plots_entry_nodes()
    #exec_cls.start_plots_build_nodes()
    args = docopt.docopt(__doc__)
    logfile = args['<flesctrl_logfile>']
    modes = args['--mode']
    verbose = bool(args['--verbose'])
    modes = validate_params(logfile,modes,verbose)
    exec_cls = execution(logfile)
    #print(modes)
    if 'flesctrl_logfile' in modes:
        #print('test1')
        exec_cls.get_data_from_logfile()
    else:
        exec_cls
    if 'create_plots' in modes:
        #print('test')
        exec_cls.start_plots_entry_nodes()
        exec_cls.start_plots_build_nodes()
    
    if 'serialization' in modes:
        exec_cls.serialize_data_rates()
    
    
def validate_params(logfile,modes,verbose):
    if not os.path.isfile(logfile):
        print('file does not exist')
        sys.exit(1)
    valid_modes = ['flesctrl_logfile','serialization','create_plots']
    #print(modes)
    for mode in modes:
        if 'all' in modes:
            modes = ['flesctrl_logfile','serialization','create_plots']
            break
        elif mode not in valid_modes:
            print('Unknown mode')
            sys.exit(1)
    #print(modes)
    return modes


if __name__ == '__main__':
    main()