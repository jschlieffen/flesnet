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
import time


# =============================================================================
# This file is the main execution file for the evaluation. When starting this 
# program one needs to give the flesctrl_logfile including path, that can be 
# found under logs/general. It consists of five different modes 
#   1. flesctrl_logfile: This mode shall be used, when the logfile from collectl
#                        and flesnet should be used to extract the data.
#                        If not set the program will use serialized data from 
#                        the benchmarking tool.
#                        Note: The program uses the names given by flesctrl.
#                              DO NOT CHANGE THE FILE NAMES!!!!!
#   2. serialization: This mode shall be used if one wants to serialize the 
#                     data rates, shm usage, cpu usage. 
#   3. check_serialization: Checks if the data serialized in a correct way.
#                           Can only be used if mode serialization is also set
#   4. create_plots: Decides whether plots should be created or not.
#   5. prev_run: This decides if a Run that can be found under the folder Runs
#                should be revaluated. This is specifically usefull, when 
#                one wants to remove certain time-intervals in order to get 
#                cleaner plots.
#   6. all: This can be used if one wants to activate all modes
# It also have the possibility to only consider certain time intervals,
# via the flags --startime=..., --endtime=... Is deactivated by default 
# =============================================================================


# =============================================================================
# Is used when --prev_run is activated. It changes the working directory from 
# this folder to the folder ../Runs/{specific_run}
# =============================================================================
def change_dir(flesctl_logfile):
    directory = os.path.splitext(os.path.basename(flesctl_logfile))[0]
    path = f"../Runs/{directory}"
    if not os.path.exists(path):
        logger.critical('Run does not exist')
        sys.exit(1)
    
    os.chdir(path)
    #print(os.getcwd())
    #print('test')
    eval_number = 0
    eval_file = f"tmp/eval_num.txt"
    if not os.path.isfile(eval_file):
        #os.mkdir("tmp")
        eval_number = 0
    else:
        with open(eval_file, "r") as file:
            eval_number = int(file.read().strip())
    with open(eval_file,"w") as file:
         file.write(str(eval_number+1))   
    
    os.mkdir(f"eval_round_{eval_number}")
    os.chdir(f"eval_round_{eval_number}")
    if not (os.path.isfile(flesctl_logfile)):
        logger.critical('file does not exist')
        sys.exit(1)
    
    logger.success(f"Run found and proceeding as eval run {eval_number}")

# ===============================================================================
# TODOs:
#        2. clean up code
#        3. comment code 
# ===============================================================================

# =============================================================================
# main execution class. It reads at first the flesctrl_logfile and then
# works together with the function main to work the different modes specified
# by the user
# =============================================================================
class execution:
    
    def __init__(self,flesctl_logfile):
        self.entry_nodes = []
        self.build_nodes = []
        self.receiving_nodes = []
        self.flesctl_logfile = flesctl_logfile
        if not (os.path.isfile(flesctl_logfile)):
            logger.critical('file does not exist')
            sys.exit(1)
        self.infiniband_used = False
        self.zeromq_used = False
        self.get_node_names(flesctl_logfile)
        self.data_rates_entry_nodes = {}
        self.shm_usages_entry_nodes = {}
        self.data_rates_build_nodes = {}
        self.shm_usages_build_nodes = {}
        self.data_rates_collectl = {}
        self.cpu_usage_collectl = {}
        self.timeslice_forwarding_activated = False

        self.prev_run = False
        self.eval_number = 0
        

        
        
    def get_node_names(self,flesctl_logfile_path):
        with open(flesctl_logfile_path, "r") as file:
            flesctl_logfile = file.read()
        pattern = re.compile(r"([a-zA-Z0-9-]+)\s+as\s+index\s+(\d+)")
        receiving_pattern = re.compile(r"([a-zA-Z0-9-]+)\s+was connected to\s+([a-zA-Z0-9-]+)")
        super_node_pattern = re.compile(
            r"([a-zA-Z0-9-]+)\s+with entry node index\s+(\d+)\s+and build node index\s+(\d+)"
        )
        nodes_info = []
        node_types = ['Entry', 'Build', 'receiving', 'Super']
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
                    elif node_type == 'Super':
                        for name, entry_idx, build_idx in re.findall(super_node_pattern, match):
                            nodes_info.append({
                                'node_name': name,
                                'node_type': 'Entry',
                                'index': int(entry_idx)
                            })
                            nodes_info.append({
                                'node_name': name,
                                'node_type': 'Build',
                                'index': int(build_idx)
                            })
        for node in nodes_info:
            if node['node_type'] == 'Entry':
                self.entry_nodes.append((node['node_name'], node['index']))
            elif node['node_type'] == 'Build':
                self.build_nodes.append((node['node_name'], node['index']))
            elif node['node_type'] == 'receiving':
                self.receiving_nodes.append((node['node_name'], node['connected_to']))
        #print(self.entry_nodes)
        #print(self.build_nodes)
        if "Infiniband" in flesctl_logfile:
            self.infiniband_used = True
        elif "Ethernet" in flesctl_logfile:
            self.infiniband_used = False
        else:
            logger.error("Did not find the connection type")
            sys.exit(1)
        if "zeromq" in flesctl_logfile:
            self.zeromq_used = True
        else:
            self.zeromq_used = False
        
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

    def get_data_collectl(self):
        self.data_rates_collectl['entry_nodes'] = {}
        self.cpu_usage_collectl['entry_nodes'] = {}
        self.data_rates_collectl['build_nodes'] = {}
        self.cpu_usage_collectl['build_nodes'] = {}
        if self.receiving_nodes != []:
            self.timeslice_forwarding_activated = True
            self.data_rates_collectl['receiving_nodes'] = {}
            self.cpu_usage_collectl['receiving_nodes'] = {}
        for entry_node in self.entry_nodes:
            Logfile_name = f"../logs/collectl/entry_nodes/entry_node_{entry_node[0]}.csv"
            Logfile_name_cpu = Logfile_name.replace('.csv', '_cpu_usage.csv')
            Logfile_reader_cls = CLR.collectl_reader(f'entry_node_{entry_node[0]}',Logfile_name, Logfile_name_cpu, 'entry_node',self.timeslice_forwarding_activated)
            if self.infiniband_used:
                Logfile_reader_cls.extract_infiniband_usage()
            else:
                Logfile_reader_cls.extract_ethernet_usage()
            Logfile_reader_cls.extract_cpu_usage()
            self.data_rates_collectl['entry_nodes'][f"entry_nodes_{entry_node[0]}"] = Logfile_reader_cls.data_rates
            self.cpu_usage_collectl['entry_nodes'][f"entry_nodes_{entry_node[0]}"] = Logfile_reader_cls.cpu_usage
        for build_node in self.build_nodes:
            Logfile_name = f"../logs/collectl/build_nodes/build_node_{build_node[0]}.csv"
            Logfile_name_cpu = Logfile_name.replace('.csv', '_cpu_usage.csv')
            Logfile_reader_cls = CLR.collectl_reader(f'build_node_{build_node[0]}',Logfile_name, Logfile_name_cpu, 'build_node',self.timeslice_forwarding_activated)
            if self.infiniband_used:
                Logfile_reader_cls.extract_infiniband_usage()
            else:
                Logfile_reader_cls.extract_ethernet_usage()
            Logfile_reader_cls.extract_cpu_usage()
            self.data_rates_collectl['build_nodes'][f"build_nodes_{build_node[0]}"] = Logfile_reader_cls.data_rates
            self.cpu_usage_collectl['build_nodes'][f"build_nodes_{build_node[0]}"] = Logfile_reader_cls.cpu_usage
        for receiving_node in self.receiving_nodes:
            Logfile_name = f"../logs/collectl/tsclient/receiving_node_{receiving_node[0]}.csv"
            Logfile_name_cpu = Logfile_name.replace('.csv', '_cpu_usage.csv')
            Logfile_reader_cls = CLR.collectl_reader(f'receiving_node_{receiving_node[0]}',Logfile_name, Logfile_name_cpu, 'tsclient', self.timeslice_forwarding_activated)
            if self.infiniband_used:
                Logfile_reader_cls.extract_infiniband_usage()
            else:
                Logfile_reader_cls.extract_ethernet_usage()
            Logfile_reader_cls.extract_cpu_usage()
            self.data_rates_collectl['receiving_nodes'][f"receiving_nodes_{receiving_node[0]}"] = Logfile_reader_cls.data_rates
            self.cpu_usage_collectl['receiving_nodes'][f"receiving_nodes_{receiving_node[0]}"] = Logfile_reader_cls.cpu_usage
        
    def serialize_data_rates(self):
        Logfile_serializer_entry_nodes = LH.serialize_data("e",self.data_rates_entry_nodes, self.shm_usages_entry_nodes, self.flesctl_logfile)
        Logfile_serializer_entry_nodes.serialize_data_rates()
        Logfile_serializer_entry_nodes.serialize_shm_usage_entry_nodes()
        Logfile_serializer_build_nodes = LH.serialize_data("b", self.data_rates_build_nodes, self.shm_usages_build_nodes, self.flesctl_logfile)
        if not self.zeromq_used:
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
        if not self.zeromq_used:
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
            
            
            diff = DeepDiff(self.data_rates_entry_nodes, data_rates, ignore_type_in_groups=[(int,float)])
            if not diff:
                logger.success('serialization process succeeded')
            else:
                logger.error('serialization process not succeeded')
                print(diff)
        deserializer_entry_nodes.deserialize_shm_usage_entry_nodes()
        shm_usage = deserializer_entry_nodes.shm_usage
        if shm_usage == self.shm_usages_entry_nodes:
            logger.success('serialization process succeeded')
        else:
            logger.error('serialization process not succeeded')
            diff = DeepDiff(self.shm_usages_entry_nodes, shm_usage, ignore_type_in_groups=[(int,float)])
            if not diff:
                logger.success('serialization process succeeded')
            else:
                logger.error('serialization process not succeeded')
                
                print(diff)
            #print(diff)
        deserialzer_build_nodes = LH.deserialize_data("b", self.flesctl_logfile)
        if not self.zeromq_used:
            deserialzer_build_nodes.deserialize_data_rates()
            data_rates_build_nodes = deserialzer_build_nodes.data_rate
            if data_rates_build_nodes == self.data_rates_build_nodes:
                logger.success('serialization process succeeded')
            else:
                logger.error('serialization process not succeeded')
                diff = DeepDiff(self.data_rates_build_nodes, data_rates_build_nodes, ignore_type_in_groups=[(int,float)])
                if not diff:
                    logger.success('serialization process succeeded')
                else:
                    logger.error('serialization process not succeeded')
                    print(diff)
            deserialzer_build_nodes.deserialize_shm_usage_build_nodes()
            shm_usage_build_nodes = deserialzer_build_nodes.shm_usage
            if shm_usage_build_nodes == self.shm_usages_build_nodes:
                logger.success('serialization process succeeded')
            else:
                logger.error('serialization process not succeeded')
                diff = DeepDiff(self.shm_usages_build_nodes, shm_usage_build_nodes, ignore_type_in_groups=[(int,float)])
                if not diff:
                    logger.success('serialization process succeeded')
                else:
                    logger.error('serialization process not succeeded')
                    print(diff)
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
            diff = DeepDiff(self.data_rates_collectl, data_rates, ignore_type_in_groups=[(int,float)])
            if not diff:
                logger.success('serialization process succeeded')
            else:
                logger.error('serialization process not succeeded')
                print(self.data_rates_collectl)
                print(data_rates)
                print(diff)
            #print(diff)
        if cpu_usage == self.cpu_usage_collectl:
            logger.success('serialization process collectl succeeded')
        else:
            logger.error('serialization process not succeeded')
            diff = DeepDiff(self.cpu_usage_collectl, cpu_usage, ignore_type_in_groups=[(int,float)])
            if not diff:
                logger.success('serialization process succeeded')
            else:
                logger.error('serialization process not succeeded')
                print(diff)
            #print(diff)
            
            
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
        #cp_cls.box_plot_data_rates()
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
        #cp_cls.box_plot_data_rates()
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
    args = docopt.docopt(__doc__)
    logfile = args['<flesctrl_logfile>']
    modes = args['--mode']
    collectl_used = bool(args['--collectl_used'])
    verbose = bool(args['--verbose'])
    starttime = args['--starttime']
    endtime = args['--endtime']
    modes = validate_params(logfile,modes,verbose)

    logger.info('starting with evaluation')
    time.sleep(10)
    if 'prev_run' in modes:
        #exec_cls.prev_run = True
        #print('test')
        change_dir(logfile)
    exec_cls = execution(logfile)
    if 'flesctrl_logfile' in modes:
        exec_cls.get_data_from_logfile()
        if collectl_used:
            exec_cls.get_data_collectl()

    else:
        exec_cls.deserialize_data()
        if collectl_used:
            exec_cls.deserialize_data_collectl()
    if 'create_plots' in modes:
        exec_cls.start_plots_entry_nodes(starttime,endtime)
        if not exec_cls.zeromq_used:
            exec_cls.start_plots_build_nodes(starttime,endtime)
        if collectl_used:
            exec_cls.start_plots_collectl(starttime, endtime)
    
    if 'serialization' in modes:
        exec_cls.serialize_data_rates()
        if collectl_used:
            exec_cls.serialize_data_rates_collectl()
    if 'check_serialization' in modes:
        exec_cls.check_deserialization() 
        if collectl_used:
            exec_cls.check_deserialization_collectl()
    
    
def validate_params(logfile,modes,verbose):
    #if not os.path.isfile(logfile):
        #logger.critical('logfile does not exist')
        #sys.exit(1)
    valid_modes = ['flesctrl_logfile','serialization','check_serialization','create_plots', 'prev_run']
    if modes == []:
        logger.warning('It is quite pointless to not do anything')
    for mode in modes:
        if 'all' in modes:
            if 'prev_run' in modes:
                modes = ['flesctrl_logfile','serialization', 'check_serialization','create_plots', 'prev_run']
            else:
                modes = ['flesctrl_logfile','serialization', 'check_serialization','create_plots']
            break
        elif mode not in valid_modes:
            logger.critical('Unknown mode')
            sys.exit(1)
    return modes


if __name__ == '__main__':
    main()
