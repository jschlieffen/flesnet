#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 15:48:03 2025

@author: jschlieffen
"""

import configparser as cfg
import os
import sys
from log_msg import *
import re
import subprocess
from datetime import datetime, timedelta

# =============================================================================
# This file reads the params from the config file and checks the validation
# =============================================================================

class Params:
    
    # =============================================================================
    # Here are the default values of the params that are not necessarily required   
    # =============================================================================
    def __init__(self,config_file):
        self.num_entrynodes = 0
        self.num_buildnodes = 0
        self.use_collectl = 0
        self.num_cpus = 2
        self.kill_nodes = 0
        self.timer_for_kill = timedelta(minutes=1)
        self.num_entrynodes_kills = 1 
        self.num_buildnodes_kills = 1
        self.num_processnodes_kills = 1
        self.revive_nodes=1
        self.set_kill_list = 0
        self.entry_node_kill_list = []
        self.build_node_kill_list = []
        self.process_node_kill_list = []
        self.set_node_list=0
        self.entry_nodes_list=[]
        self.build_nodes_list=[]
        self.path = ""
        self.transport_method = ""
        self.use_infiniband = 1
        self.customize_string = "" 
        self.use_pattern_gen = 0
        self.use_dmsa_files = 0
        self.input_files = []
        self.activate_timesliceforwarding = 0
        self.write_data_to_file = ""
        self.analyze_data = 0
        self.port = 0
        self.show_total_data = 0
        self.enable_graph = 0
        self.enable_progress_bar = 0
        self.show_only_entry_nodes = 0
        self.use_grafana = 0
        self.influx_node_ip = ""
        self.influx_token = ""
        self.overlap_usage_of_nodes = 0
        self.config = cfg.ConfigParser(interpolation=None)
        self.config.read(config_file)
        self.get_params(config_file)
        
    # =============================================================================
    # only for debug purposes    
    # =============================================================================
    def __str__(self):
        attributes = ', '.join(f"{key}={value}" for key, value in self.__dict__.items())
        return f"{self.__class__.__name__}({attributes})"
    
    
    # =============================================================================
    # gets the params for the different params and defines if they are required 
    # or not 
    # =============================================================================
    def get_params(self, config_file):        
        self.get_num_nodes_par()
        self.get_general_par()
        self.get_kill_par()
        self.get_node_list_par()
        self.get_flesnet_par()
        self.get_mstool_par()
        self.get_tsclient_par()
        self.get_mon_par()
        self.get_influx_par()

    def get_num_nodes_par(self):
        self.num_entrynodes = self.get_value('Number_of_Nodes', 'entry_nodes', 'int', required=True)
        self.num_buildnodes = self.get_value('Number_of_Nodes', 'build_nodes', 'int', required=True)
        
    def get_general_par(self):
        self.use_collectl = self.get_value('general', 'use_collectl','int',required=True)
        self.num_cpus = self.get_value('general', 'num_cpus', 'int', required=False)
        self.overlap_usage_of_nodes = self.get_value('general', 'overlap_usage_of_nodes', 'int', self.overlap_usage_of_nodes, False)
        
    def get_kill_par(self):
        self.kill_nodes = self.get_value('robustness_test', 'kill_nodes_during_execution', 'int',self.kill_nodes, required=False)
        self.timer_for_kill = self.get_value('robustness_test', 'timer_for_kills', 'time', self.timer_for_kill, required=False)
        self.num_entrynodes_kills = self.get_value('robustness_test', 'num_entry_nodes_kills', 'int' , self.num_entrynodes_kills, required=False)
        self.num_buildnodes_kills = self.get_value('robustness_test', 'num_build_nodes_kills', 'int' , self.num_buildnodes_kills, required=False)
        self.num_processnodes_kills = self.get_value('robustness_test', 'num_process_nodes_kills', 'int' , self.num_processnodes_kills, required=False)
        self.revive_nodes=self.get_value('robustness_test', 'revive_nodes', 'int' , self.revive_nodes, required=False)
        self.set_kill_list = self.get_value('robustness_test', 'set_kill_list', 'int' , self.set_kill_list, required=False)
        self.entry_node_kill_list = self.get_node_list('robustness_test', 'entry_node_kill_list', self.entry_node_kill_list, False)
        self.build_node_kill_list = self.get_node_list('robustness_test', 'build_node_kill_list', self.build_node_kill_list, False)
        self.process_node_kill_list = self.get_node_list('robustness_test', 'process_node_kill_list', self.process_node_kill_list, False)
    
    
# =============================================================================
#     TODO: make node list for timeslice-forwarding
# =============================================================================
    def get_node_list_par(self):
        self.set_node_list = self.get_value('set_node_list', 'set_node_list', 'int',self.set_node_list, False)
        self.entry_nodes_list = self.get_node_list('set_node_list', 'entry_nodes_list', self.entry_nodes_list, False)
        self.build_nodes_list = self.get_node_list('set_node_list', 'build_nodes_list', self.build_nodes_list, False)
        
    def get_flesnet_par(self):
        self.path = self.get_value('flesnet_commands', 'path_to_flesnet', 'str', required=True)
        self.transport_method = self.get_value('flesnet_commands', 'transport_method', 'str', required=True)
        self.use_infiniband = self.get_value('flesnet_commands','use_infiniband','int', self.use_infiniband, False)
        self.customize_string = self.get_value('flesnet_commands', 'customize_string', 'str', True)
    
    def get_mstool_par(self):
        self.use_pattern_gen = self.get_value('mstool_commands', 'use_pattern_gen', 'int', self.use_pattern_gen, False)
        self.use_dmsa_files = self.get_value('mstool_commands', 'use_dmsa_files', 'int', self.use_dmsa_files, False)
        self.input_files = self.get_input_file_list('input_file')
    
    def get_tsclient_par(self):
        self.activate_timesliceforwarding = self.get_value('tsclient_commands', 'activate_timesliceforwarding','int', True)
        self.write_data_to_file = self.get_value('tsclient_commands', 'write_data_to_file', 'str', self.write_data_to_file, False)
        self.analyze_data = self.get_value('tsclient_commands', 'analyze_data', 'str', self.analyze_data, False)
        self.port = self.get_value('tsclient_commands', 'port', 'str', self.port, False)
        
    def get_mon_par(self):
        self.show_total_data = self.get_value('Monotoring', 'show_total_data', 'int', True)
        self.enable_graph = self.get_value('Monotoring', 'show_graph', 'int', False)
        self.enable_progress_bar = self.get_value('Monotoring', 'show_progress_bar', 'int', self.enable_progress_bar, False)
        self.show_only_entry_nodes = self.get_value('Monotoring', 'show_only_entry_nodes', 'int', self.show_only_entry_nodes, False)
        
    def get_influx_par(self):
        self.use_grafana = self.get_value('influxdb', 'use_grafana', 'int', True)
        self.influx_node_ip = self.get_value('influxdb', 'influx_node_ip','str', self.influx_node_ip, False)
        self.influx_token = self.get_value('influxdb', 'token','str', self.influx_token, False)

    
    def get_value(self, section, param, par_type, var=None, required=False):
        val = os.getenv(param)
        
        if val is not None:
            if par_type=='int':
                return int(val)
            elif par_type == 'time':
                time_str = self.config.get(section, param)
                h, m, s = map(int, time_str.split(":"))
                return timedelta(hours=h, minutes=m, seconds=s)
            return val
        elif self.config.has_option(section, param):
            if par_type == 'int':
                return self.config.getint(section, param)
            elif par_type == 'time':
                time_str = self.config.get(section, param)
                h, m, s = map(int, time_str.split(":"))
                return timedelta(hours=h, minutes=m, seconds=s)
            else:
                return self.config.get(section, param)
        elif required:
            logger.critical(f'required Param not set: {param}')
            sys.exit(1)
        else:
            logger.warning(f'not required Param not set: {param}')
            return var
        
    def get_input_file_list(self,section):
        file_list = []
        
        for entry in self.config[section]:
            if '_data' not in entry:
                path = self.config['input_file'][entry]
                data_size_name = entry + '_data'
                if self.config.has_option('input_file', data_size_name):
                    data_size = self.config.getint('input_file', data_size_name)
                    file_list.append((entry,path,data_size))
                else:
                    file_list.append((entry, path))
        return file_list

    def get_list(self,section, param, var=None, required=False):
        val = os.getenv(param)
        
        if val is not None:
            return val.split(',')
        elif self.config.has_option(section, param):
            list_str = self.config.get(section,param)
            val = [item.strip() for item in list_str.split(',')]
            return val
        elif required:
            logger.critical(f'required Param not set: {param}')
            sys.exit(1)
        else:
            logger.warning(f'not required Param not set: {param}')
            return var
            
    def get_node_list(self,section,param, var=None, required=False):
        node_list = []
        node_str = os.getenv(param)
        if node_str is None:
            node_str = self.config.get(section,param)
        range_pattern = re.findall(r'(.*?)(\d+)-(\d+)', node_str)
        list_pattern = re.findall(r'(.*?)(\d+(?:,\d+)*)', node_str)
        for base, start, end in range_pattern:
            start, end = int(start), int(end)
            if start < 10:
                node_list.extend([f"htc-cmp00{i}" for i in range(start, end + 1)])
            elif start < 100:    
                node_list.extend([f"htc-cmp0{i}" for i in range(start, end + 1)])
            else:
                node_list.extend([f"htc-cmp{i}" for i in range(start, end + 1)])
        for base, numbers in list_pattern:
            num_list = numbers.split(",")
            node_list.extend([f"htc-cmp{num.strip()}" for num in num_list])
        node_list = sorted(set(node_list))
        return node_list

        

    def validation_params(self, system_check):
        Params_check = params_checker(self, system_check)
        Params_check.check_validity_of_files()
            
        if self.set_node_list:
            Params_check.check_nodes_exist()
            
        if os.getenv('SLURM_JOB_NUM_NODES'):
            Params_check.check_num_nodes()
            if self.set_node_list:
                Params_check.check_req_nodes_alloc
        if self.kill_nodes:
            Params_check.check_kill_par()
        self.show_only_entry_nodes = Params_check.check_transport_method()
        self.enable_progress_bar = Params_check.monitoring_check()
        Params_check.check_timeslice_forwarding()
        return Params_check.Params_valid


# =============================================================================
# This class checks the different parameters from the config file. Is currently
# used in before the start of flesctrl and in the setup checker .
# Might be extended in the future.
# =============================================================================
class params_checker:
    
    def __init__(self, params, system_check):
        self.Par_ = params
        self.system_check = system_check
        self.Params_valid = True
        
    def exit_program(self):
        if not self.system_check:
            logger.error("Invalid config. Shutdown program")
            sys.exit(1)
        self.Params_valid = False
    
    def check_validity_of_files(self):
        if self.Par_.use_pattern_gen != 1:
            if not self.Par_.input_files:
                logger.critical('no input files and no usage of the pattern generator')
                self.exit_program()
            else:
                for elem in self.Par_.input_files:
                    if not os.path.isfile(elem[1]):
                        logger.critical(f'File {elem[1]} does not exist')
                        self.exit_program()
    
    def check_program_exists(self):
        for program in ['./mstool', './flesnet']:
            program_path = self.Par_.path + program
            if not (os.path.isfile(program_path) and os.access(program_path, os.X_OK)):
                logger.critical(f'Program {program} does not exist')
                self.exit_program()

    def check_num_nodes(self):
        if self.Par_.overlap_usage_of_nodes == 1:
            num_tot_nodes_req = max(self.Par_.num_buildnodes, self.Par_.entry_nodes) 

            if self.Par_.set_node_list:
                num_nodes_req_list = max(len(self.Par_.entry_nodes_list), len(self.Par_.build_nodes_list))
        else:
            num_tot_nodes_req = self.Par_.num_buildnodes + self.Par_.num_entrynodes

            if self.Par_.set_node_list:
                num_nodes_req_list = len(set(self.Par_.entry_nodes_list  + self.Par_.build_nodes_list))
        if self.Par_.activate_timesliceforwarding:
            num_tot_nodes_req += self.Par_.num_buildnodes
        num_nodes_get = int(os.getenv('SLURM_JOB_NUM_NODES'))
        if num_tot_nodes_req < num_nodes_get:
            logger.warning(f"Too many nodes allocated: Required: {num_tot_nodes_req}, Got: {num_nodes_get}. Remaining nodes are unused")
        if num_tot_nodes_req > num_nodes_get:
            logger.critical(f"Not enough nodes allocated. Expected: {num_tot_nodes_req}, Got: {num_nodes_get}.")
            self.exit_program()
        if self.Par_.set_node_list:
            if num_nodes_req_list < num_tot_nodes_req:
                logger.warning(f"Not all nodes that are required are set. Fill the remaining ones automatically")
            if num_nodes_req_list > num_tot_nodes_req:
                logger.critical(f"More nodes are set in the node list, then are required.")
                self.exit_program()
    
    
        
    def check_nodes_exist(self):
        try:
            cmd = ["sinfo", "-N", "-h", "-o", "%N %f"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            node_features = {}
            for line in result.stdout.strip().splitlines():
                if not line.strip():
                    continue
                parts = line.strip().split(None, 1)
                node = parts[0]
                features = parts[1] if len(parts) > 1 else ""
                node_features[node] = features    
            for node in self.Par_.entry_nodes_list:
                if node not in node_features:
                    logger.critical(f"Entrynode: {node} not found on the cluster")
                    self.exit_program()
                if self.Par_.use_infiniband:
                    features = node_features[node]
                    #print(features.lower())
                    if "infiniband" not in features.lower():
                        logger.critical(f"Entrynode: {node} does not provide Infiniband")
                        self.exit_program()
            for node in self.Par_.build_nodes_list:
                if node not in node_features:
                    logger.critical(f"Buildnode: {node} not found on the cluster")
                    self.exit_program()
                if self.Par_.use_infiniband:
                    features = node_features[node]
                    if "infiniband" not in features.lower():
                        logger.critical(f"Buildnode: {node} does not provide Infiniband")
                        self.exit_program()
                        
        except subprocess.CalledProcessError as e:
            logger.error(f"[!] Error running sinfo: {e} Cannot check the validity of the given nodelist")

    def check_req_nodes_alloc(self):
        node_str = os.environ.get('SLURM_NODELIST')
        node_list = []
        if node_str is None:
            logger.critical('SLURM_NODELIST is not set, Maybe you forget to allocate the nodes')
            self.exit_program()
        range_pattern = re.findall(r'(.*?)(\d+)-(\d+)', node_str)
        list_pattern = re.findall(r'(.*?)(\d+(?:,\d+)*)', node_str)
        for base, start, end in range_pattern:
            start, end = int(start), int(end)
            if start < 10:
                node_list.extend([f"htc-cmp00{i}" for i in range(start, end + 1)])
            elif start < 100:    
                node_list.extend([f"htc-cmp0{i}" for i in range(start, end + 1)])
            else:
                node_list.extend([f"htc-cmp{i}" for i in range(start, end + 1)])
        for base, numbers in list_pattern:
            num_list = numbers.split(",")
            node_list.extend([f"htc-cmp{num.strip()}" for num in num_list])
        node_list = sorted(set(node_list))
        for entry_node in self.Par_.entry_nodes_list:
            if entry_node not in node_list:
                logger.critical(f"required entry node: {entry_node} not allocated")
                self.exit_program()
        for build_node in self.Par_.build_nodes_list:
            if build_node not in node_list:
                logger.critical(f"required build node: {build_node} not allocated")
                self.exit_program()
                
    def check_kill_par(self):
        if self.Par_.timer_for_kill == timedelta(seconds=0):
            logger.critical("Cannot kill programs immediatly")
            self.exit_program()
        if self.Par_.activate_timesliceforwarding == 0 and self.Par_.num_processnodes_kills > 0:
            logger.warning("Cannot kill process nodes. Timeslice-forwarding is deactivated")
        if self.Par_.num_entrynodes_kills > self.Par_.num_entrynodes:
            logger.critical(f"Too many entry node kills: num entry nodes total: {self.Par_.num_entrynodes}, entry node kills: :{self.Par_.num_entrynodes_kills}")
            self.exit_program()
        if self.Par_.num_buildnodes_kills > self.Par_.num_buildnodes:
            logger.critical(f"Too many build node kills: num build nodes total: {self.Par_.num_buildnodes}, build node kills: :{self.Par_.num_buildnodes_kills}")
            self.exit_program()
        if self.Par_.num_processnodes_kills > self.Par_.num_buildnodes:
            logger.critical(f"Too many process node kills: num process nodes total: {self.Par_.num_buildnodes}, process node kills: :{self.Par_.num_processnodes_kills}")
            self.exit_program()
        if self.Par_.set_kill_list:
            if not self.Par_.set_node_list:
                logger.critical("Node list is not set, but kill list. Might happen that nodes are gonna be killed that are not part of the allocation")
                self.exit_program()
            for kill_entry in self.Par_.entry_node_kill_list:
                if kill_entry not in self.Par_.entry_nodes_list:
                    logger.critical(f"Supposed to kill entry node: {kill_entry}. But this is not contained in the entry nodes list")
                    self.exit_program()
            for kill_build in self.Par_.build_node_kill_list:
                if kill_build not in self.Par_.build_nodes_list:
                    logger.critical(f"Supposed to kill build node: {kill_build}. But this is not contained in the build nodes list")
                    self.exit_program()
                        
            #TODO: Repeat for process nodes once implemented
                

    def check_transport_method(self):
        if self.Par_.transport_method not in ['zeromq', 'rdma']:
            if self.Par_.transport_method == 'libfabric':
                logger.critical("Transport method libfabric is currently not working.")
            else:
                logger.critical(f"unknown transport method: {self.Par_.transport_method}")
            self.exit_program()
        if self.Par_.transport_method == 'rdma' and self.Par_.use_infiniband == 0:
            logger.critical("Transport method RDMA does not support ethernet connection")
            self.exit_program()
        if self.Par_.transport_method == 'zeromq' and self.show_only_entry_nodes == 0:
            logger.warning(f'transport method zeromq only shows data rate for the entry nodes. Therefore param show_only_entry_nodes is set to 1')
            return 1
        return 0

    def monitoring_check(self):
        if self.Par_.enable_progress_bar:
            if self.Par_.use_pattern_gen == 1:
                logger.warning('Pattern Generator is used, thus there is no limit for the total data. Therefore progress bar is disabled')
                return 0
        return 1
    
    def check_timeslice_forwarding(self):
        if self.Par_.activate_timesliceforwarding == 1:
            if int(self.Par_.port) < 1023:
                logger.critical(f"used port for timeslice-forwarding: {self.Par_.port} is privileged, thus cannot be used")
                self.exit_program()
            if f"tcp://*:{self.Par_.port}" not in self.Par_.customize_string:
                logger.critical(f"used port for timeslice-forwarding: {self.Par_.port} does not coincide with the port used in flesnet")
                self.exit_program()
            if self.Par_.write_data_to_file != '0':
                logger.warning(f"The .tsa file is written in {self.Par_.path} unless you gave a path to the output file")
    

