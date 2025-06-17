#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#Created on Fri Apr 25 15:41:42 2025

#@author: jschlieffen

"""
Usage: 
    execution.py <flesctrl_logfile> [--verbose] [--collectl_used] [--mode=<mode>...] [--starttime=<starttime>] [--endtime=<endtime>]
    
Options:
    <flesctrl_logfile>             The general logfile of the flesctrl
    --verbose                      flag for verbose mode [default: False]
    --collectl_used                Decides whether collectl was used to track data or not [default: False]
    --mode=<mode>...               The mode for the execution (deserialization/plots etc.) [default: all]
    --starttime=<starttime>        The start time if only a given interval should be printed. Have to be passed like 13:45:00 [default: 00:00:00]
    --endtime=<endtime>            The end time if only a given interval should be printed. Have to be passed like 13:45:00 [default: 00:00:00]
"""



import Logfile_reader as LR
import Logfile_handler as LH
import collectl_logfile_reader as CLR
import collectl_Logfile_handler as CLH
import plots 
import plots_collectl as Cplots
import re
import docopt
import os
import sys
from pathlib import Path
#sys.path.append(os.path.dirname(os.path.abspath(__file__)))
#print(__file__)
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '..'))
os.environ['write_logfile'] = '0'
from log_msg import *
script_dir = Path(__file__).resolve().parent
os.chdir(script_dir)
#sys.path.append(os.path.abspath('../'))

from deepdiff import DeepDiff
from datetime import datetime


# ===============================================================================
# TODOs: 1. implement cpu usage plots for allocated cpus                done
#        2. implement deserialization/serialization for collectl data   make for cpu usage
#        3. make folder structure for plots/data depending on run id and timestmp   done
#        4. get more cpus in allocation, when timeslice-forwarding is used          done/make num cpus per node a param
#        5. clean up code
#        6. comment code 
# ===============================================================================
class execution:
    
    def __init__(self,flesctl_logfile):
        self.entry_nodes = []
        self.build_nodes = []
        self.receiving_nodes = []
        self.flesctl_logfile = flesctl_logfile
        if not (os.path.isfile(flesctl_logfile)):
            logger.critical('file does not exist')
            sys.exit(1)
        self.get_node_names(flesctl_logfile)
        self.data_rates_entry_nodes = {}
        self.shm_usages_entry_nodes = {}
        self.data_rates_build_nodes = {}
        self.shm_usages_build_nodes = {}
        self.data_rates_collectl = {}
        self.cpu_usage_collectl = {}
        self.timeslice_forwarding_activated = False
        
    def get_node_names(self,flesctl_logfile_path):
        with open(flesctl_logfile_path, "r") as file:
            flesctl_logfile = file.read()
        pattern = re.compile(r"([a-zA-Z0-9-]+)\s+as\s+index\s+(\d+)")
        receiving_pattern = re.compile(r"([a-zA-Z0-9-]+)\s+was connected to\s+([a-zA-Z0-9-]+)")
        nodes_info = []
        node_types = ['Entry', 'Build', 'receiving']
        for node_type in node_types:
            matches = re.findall(f'{node_type} nodes:([\s\S]*?)(?=\n[A-Za-z]|$)', flesctl_logfile)
            if matches:
                for match in matches:
                    if node_type in ['Entry', 'Build']:
                        for name, index in re.findall(pattern, match):
                            nodes_info.append({
                                'node_name': name,
                                'node_type': node_type,
                                'index': int(index)
                            })
                    elif node_type == 'receiving':
                        for recv_name, build_name in re.findall(receiving_pattern, match):
                            nodes_info.append({
                                'node_name': build_name,
                                'node_type': node_type,
                                'connected_to': recv_name
                            })
        for node in nodes_info:
            if node['node_type'] == 'Entry':
                self.entry_nodes.append((node['node_name'], node['index']))
            elif node['node_type'] == 'Build':
                self.build_nodes.append((node['node_name'], node['index']))
            elif node['node_type'] == 'receiving':
                self.receiving_nodes.append((node['node_name'], node['connected_to']))

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

    def get_data_collectl(self):
        self.data_rates_collectl['entry_nodes'] = {}
        self.cpu_usage_collectl['entry_nodes'] = {}
        self.data_rates_collectl['build_nodes'] = {}
        self.cpu_usage_collectl['build_nodes'] = {}
        if self.receiving_nodes != []:
            #print('test12344')
            self.timeslice_forwarding_activated = True
            self.data_rates_collectl['receiving_nodes'] = {}
            self.cpu_usage_collectl['receiving_nodes'] = {}
        for entry_node in self.entry_nodes:
            Logfile_name = f"../logs/collectl/entry_nodes/entry_node_{entry_node[0]}.csv"
            Logfile_name_cpu = Logfile_name.replace('.csv', '_cpu_usage.csv')
            Logfile_reader_cls = CLR.collectl_reader(f'entry_node_{entry_node[0]}',Logfile_name, Logfile_name_cpu, 'entry_node',self.timeslice_forwarding_activated)
            Logfile_reader_cls.extract_infiniband_usage()
            Logfile_reader_cls.extract_cpu_usage()
            self.data_rates_collectl['entry_nodes'][f"entry_nodes_{entry_node[0]}"] = Logfile_reader_cls.data_rates
            self.cpu_usage_collectl['entry_nodes'][f"entry_nodes_{entry_node[0]}"] = Logfile_reader_cls.cpu_usage
        for build_node in self.build_nodes:
            Logfile_name = f"../logs/collectl/build_nodes/build_node_{build_node[0]}.csv"
            Logfile_name_cpu = Logfile_name.replace('.csv', '_cpu_usage.csv')
            Logfile_reader_cls = CLR.collectl_reader(f'build_node_{build_node[0]}',Logfile_name, Logfile_name_cpu, 'build_node',self.timeslice_forwarding_activated)
            Logfile_reader_cls.extract_infiniband_usage()
            Logfile_reader_cls.extract_cpu_usage()
            self.data_rates_collectl['build_nodes'][f"build_nodes_{build_node[0]}"] = Logfile_reader_cls.data_rates
            self.cpu_usage_collectl['build_nodes'][f"build_nodes_{build_node[0]}"] = Logfile_reader_cls.cpu_usage
        for receiving_node in self.receiving_nodes:
            #print(receiving_node)
            Logfile_name = f"../logs/collectl/tsclient/receiving_node_{receiving_node[0]}.csv"
            Logfile_name_cpu = Logfile_name.replace('.csv', '_cpu_usage.csv')
            Logfile_reader_cls = CLR.collectl_reader(f'receiving_node_{receiving_node[0]}',Logfile_name, Logfile_name_cpu, 'tsclient', self.timeslice_forwarding_activated)
            Logfile_reader_cls.extract_infiniband_usage()
            Logfile_reader_cls.extract_cpu_usage()
            #print(Logfile_reader_cls.data_rates)
            self.data_rates_collectl['receiving_nodes'][f"receiving_nodes_{receiving_node[0]}"] = Logfile_reader_cls.data_rates
            self.cpu_usage_collectl['receiving_nodes'][f"receiving_nodes_{receiving_node[0]}"] = Logfile_reader_cls.cpu_usage
        
    def serialize_data_rates(self):
        Logfile_serializer_entry_nodes = LH.serialize_data("e",self.data_rates_entry_nodes, self.shm_usages_entry_nodes, self.flesctl_logfile)
        Logfile_serializer_entry_nodes.serialize_data_rates()
        Logfile_serializer_entry_nodes.serialize_shm_usage_entry_nodes()
        Logfile_serializer_build_nodes = LH.serialize_data("b", self.data_rates_build_nodes, self.shm_usages_build_nodes, self.flesctl_logfile)
        Logfile_serializer_build_nodes.serialize_data_rates()
        Logfile_serializer_build_nodes.serialize_shm_usage_build_nodes()
        logger.success('serialization process finished')
        
    def serialize_data_rates_collectl(self):
        Logfile_serializer = CLH.serialize_data(self.data_rates_collectl, self.cpu_usage_collectl, self.flesctl_logfile, self.timeslice_forwarding_activated)
        Logfile_serializer.serialize_data()
        Logfile_serializer.serialize_cpu_usage()
    
    def deserialize_data(self):
        deserializer_entry_nodes = LH.deserialize_data("e",self.flesctl_logfile)
        deserializer_entry_nodes.deserialize_data_rates()
        self.data_rates_entry_nodes = deserializer_entry_nodes.data_rate
        deserializer_entry_nodes.deserialize_shm_usage_entry_nodes()
        self.shm_usages_entry_nodes = deserializer_entry_nodes.shm_usage
        deserialzer_build_nodes = LH.deserialize_data("b", self.flesctl_logfile)
        deserialzer_build_nodes.deserialize_data_rates()
        self.data_rates_build_nodes = deserialzer_build_nodes.data_rate
        deserialzer_build_nodes.deserialize_shm_usage_build_nodes()
        self.shm_usages_build_nodes = deserialzer_build_nodes.shm_usage
    
    def deserialize_data_collectl(self):
        Logfile_deserializer = CLH.deserialize_data(self.flesctl_logfile, self.timeslice_forwarding_activated)
        Logfile_deserializer.deserialize_data()
        Logfile_deserializer.deserialize_cpu_usage()
        self.data_rates_collectl = Logfile_deserializer.data_rate
        self.cpu_usage_collectl = Logfile_deserializer.cpu_usage
        
        
    def check_deserialization(self):
        self.serialize_data_rates()
        deserializer_entry_nodes = LH.deserialize_data("e",self.flesctl_logfile)
        deserializer_entry_nodes.deserialize_data_rates()
        data_rates = deserializer_entry_nodes.data_rate
        if data_rates == self.data_rates_entry_nodes:
            logger.success('serialization process succeeded')
        else:
            logger.error('serialization process not succeeded')
            #print(self.data_rates_entry_nodes)
            diff = DeepDiff(self.data_rates_entry_nodes, data_rates)
            #print(diff)
            #print(data_rates)
        deserializer_entry_nodes.deserialize_shm_usage_entry_nodes()
        shm_usage = deserializer_entry_nodes.shm_usage
        if shm_usage == self.shm_usages_entry_nodes:
            logger.success('serialization process succeeded')
        else:
            logger.error('serialization process not succeeded')
            diff = DeepDiff(self.shm_usages_entry_nodes, shm_usage)
            #print(self.shm_usages_entry_nodes)
            #print(diff)
            #print(self.shm_usages_entry_nodes['entry_node_htc-cmp506'][datetime(2025, 4, 25, 15, 27, 59)])
            #print(shm_usage['entry_node_htc-cmp506'][datetime(2025, 4, 25, 15, 27, 59)])
        deserialzer_build_nodes = LH.deserialize_data("b", self.flesctl_logfile)
        deserialzer_build_nodes.deserialize_data_rates()
        data_rates_build_nodes = deserialzer_build_nodes.data_rate
        if data_rates_build_nodes == self.data_rates_build_nodes:
            logger.success('serialization process succeeded')
        else:
            logger.error('serialization process not succeeded')
            diff = DeepDiff(self.data_rates_build_nodes, data_rates_build_nodes)
            #print(diff)
        deserialzer_build_nodes.deserialize_shm_usage_build_nodes()
        shm_usage_build_nodes = deserialzer_build_nodes.shm_usage
        if shm_usage_build_nodes == self.shm_usages_build_nodes:
            logger.success('serialization process succeeded')
        else:
            logger.error('serialization process not succeeded')
            diff = DeepDiff(self.shm_usages_build_nodes, shm_usage_build_nodes)
            #print(diff)
            #for key, vals in shm_usage_build_nodes.items():
                #for key1,vals1 in vals.items():
                    #print(f'dict: {key}, entry: {key1}')
                    #print(vals)
                    #print(self.shm_usages_build_nodes[key])
                    #diff = DeepDiff(self.shm_usages_build_nodes[key][key1],vals1)
                    #print(diff)


    def check_deserialization_collectl(self):
        self.serialize_data_rates_collectl()
        Logfile_deserializer = CLH.deserialize_data(self.flesctl_logfile, self.timeslice_forwarding_activated)
        Logfile_deserializer.deserialize_data()
        Logfile_deserializer.deserialize_cpu_usage()
        data_rates = Logfile_deserializer.data_rate
        cpu_usage = Logfile_deserializer.cpu_usage
        if data_rates == self.data_rates_collectl:
            logger.success('serialization process for collectl succeeded')
        else:
            logger.error('serialization process not succeeded')
            diff = DeepDiff(self.data_rates_collectl, data_rates)
            #print(data_rates)
            #print(self.data_rates_collectl)
            print(diff)
        if cpu_usage == self.cpu_usage_collectl:
            logger.success('serialization process collectl succeeded')
        else:
            logger.error('serialization process not succeeded')
            diff = DeepDiff(self.cpu_usage_collectl, cpu_usage)
            #print(cpu_usage)
            #print(self.cpu_usage_collectl)
            print(diff)
            
            
    def start_plots_entry_nodes(self,starttime,endtime):

        cp_cls = plots.create_plots_entry_nodes(self.data_rates_entry_nodes, self.shm_usages_entry_nodes,starttime,endtime)
        cp_cls.plot_total_data_rate()
        cp_cls.plot_avg_data_rate()
        cp_cls.plot_data_rate_single()
        cp_cls.plot_data_rate_mean_max_min()
        cp_cls.box_plot_data_rates()
        cp_cls.bar_plots_data_rates()
        cp_cls.plot_shm_usage()
        cp_cls.plot_shm_usage_single()
        logger.success('created plots for entry nodes')

    def start_plots_build_nodes(self,starttime,endtime):
        cp_cls = plots.create_plots_build_nodes(self.data_rates_build_nodes, self.shm_usages_build_nodes,starttime,endtime)
        cp_cls.plot_total_data_rate()
        cp_cls.plot_avg_data_rate()
        cp_cls.plot_data_rate_single()
        cp_cls.plot_data_rate_mean_max_min()
        cp_cls.box_plot_data_rates()
        cp_cls.bar_plots_data_rates()
        cp_cls.plot_shm_usage_assemble()
        cp_cls.plot_shm_usage_single_node_avg()
        cp_cls.plot_shm_usage_single_node_single_entry_node()
        logger.success('created plots for build nodes')
        
    def start_plots_collectl(self,starttime,endtime):
        
        cp_cls = Cplots.create_plots_collectl(self.data_rates_collectl, self.cpu_usage_collectl ,self.timeslice_forwarding_activated, starttime,endtime)
        cp_cls.plot_total_data_rate()
        cp_cls.plot_avg_data_rate()
        cp_cls.plot_data_rate_mean_max_min()
        cp_cls.plot_data_rate_single()
        cp_cls.bar_plots_data_rates()
        cp_cls.plot_cpu_usage_avg()
        logger.success('created plots from collectl data')



    def start_plots_entry_nodes(self,starttime,endtime):

        cp_cls = plots.create_plots_entry_nodes(self.data_rates_entry_nodes, self.shm_usages_entry_nodes,starttime,endtime)
        cp_cls.plot_total_data_rate()
        cp_cls.plot_avg_data_rate()
        cp_cls.plot_data_rate_single()
        cp_cls.plot_data_rate_mean_max_min()
        cp_cls.box_plot_data_rates()
        cp_cls.bar_plots_data_rates()
        cp_cls.plot_shm_usage()
        cp_cls.plot_shm_usage_single()
        logger.success('created plots for entry nodes')

    def start_plots_build_nodes(self,starttime,endtime):
        cp_cls = plots.create_plots_build_nodes(self.data_rates_build_nodes, self.shm_usages_build_nodes,starttime,endtime)
        cp_cls.plot_total_data_rate()
        cp_cls.plot_avg_data_rate()
        cp_cls.plot_data_rate_single()
        cp_cls.plot_data_rate_mean_max_min()
        cp_cls.box_plot_data_rates()
        cp_cls.bar_plots_data_rates()
        cp_cls.plot_shm_usage_assemble()
        cp_cls.plot_shm_usage_single_node_avg()
        cp_cls.plot_shm_usage_single_node_single_entry_node()
        logger.success('created plots for build nodes')
        
    def start_plots_collectl(self,starttime,endtime):
        
        cp_cls = Cplots.create_plots_collectl(self.data_rates_collectl, self.cpu_usage_collectl ,self.timeslice_forwarding_activated, starttime,endtime)
        cp_cls.plot_total_data_rate()
        cp_cls.plot_avg_data_rate()
        cp_cls.plot_data_rate_mean_max_min()
        cp_cls.plot_data_rate_single()
        cp_cls.bar_plots_data_rates()
        cp_cls.plot_cpu_usage_avg()
        cp_cls.plot_cpu_usage_single()
        logger.success('created plots from collectl data')

def main():
    
    #exec_cls = execution("../logs/general/Run_13_2025-04-25-15-28-00.log")
    #exec_cls.start_plots_entry_nodes()
    #exec_cls.start_plots_build_nodes()
    args = docopt.docopt(__doc__)
    logfile = args['<flesctrl_logfile>']
    modes = args['--mode']
    collectl_used = bool(args['--collectl_used'])
    verbose = bool(args['--verbose'])
    starttime = args['--starttime']
    endtime = args['--endtime']
    #print(starttime)
    #print(endtime)
    modes = validate_params(logfile,modes,verbose)
    exec_cls = execution(logfile)
    #print(modes)
    if 'flesctrl_logfile' in modes:
        #print('test1')
        exec_cls.get_data_from_logfile()
        if collectl_used:
            exec_cls.get_data_collectl()
            #print(exec_cls.data_rates_collectl)
            #print(exec_cls.cpu_usage_collectl)
            
    else:
        exec_cls.deserialize_data()
        if collectl_used:
            exec_cls.deserialize_data_collectl()
    if 'create_plots' in modes:
        #print('test')
        exec_cls.start_plots_entry_nodes(starttime,endtime)
        exec_cls.start_plots_build_nodes(starttime,endtime)
        if collectl_used:
            exec_cls.start_plots_collectl(starttime, endtime)
    
    if 'serialization' in modes:
        exec_cls.serialize_data_rates()
        if collectl_used:
            exec_cls.serialize_data_rates_collectl()
        #exec_cls.deserialize_data() 
    if 'check_serialization' in modes:
        exec_cls.check_deserialization() 
        if collectl_used:
            exec_cls.check_deserialization_collectl()
    
    
def validate_params(logfile,modes,verbose):
    if not os.path.isfile(logfile):
        logger.critical('logfile does not exist')
        sys.exit(1)
    valid_modes = ['flesctrl_logfile','serialization','check_serialization','create_plots']
    #print(modes)
    if modes == []:
        logger.warning('It is quite pointless to not do anything')
        #sys.exit(1)
    for mode in modes:
        if 'all' in modes:
            modes = ['flesctrl_logfile','serialization', 'check_serialization','create_plots']
            break
        elif mode not in valid_modes:
            logger.critical('Unknown mode')
            sys.exit(1)
    #print(modes)
    
    return modes


if __name__ == '__main__':
    main()