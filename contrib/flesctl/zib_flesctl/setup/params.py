#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 15:48:03 2025

@author: jschlieffen
"""

import configparser as cfg
import os
import sys
import glob
from influxdb_client import InfluxDBClient
from influxdb_client.rest import ApiException

import re
import subprocess
from datetime import datetime, timedelta
from logging_lib.log_msg import *
# =============================================================================
# This file reads the params from the config file and checks the validation
# =============================================================================

class Params:
    
    # =============================================================================
    # Here are the default values of the params that are not necessarily required   
    # =============================================================================
    def __init__(self,config_file):
        self.num_receivers = 0
        self.use_collectl = 0
        self.num_cpus = 2
        self.mem="64GB"
        self.loglevel="DEBUG"
        self.activate_robustness_test = 1
        self.timer_for_kills= timedelta(minutes=1)
        self.num_min_sender_nodes_alive=2
        self.num_min_process_nodes_alive=2
        self.num_min_input_nodes_alive=2
        self.num_min_central_manager_alive=2
        self.num_min_output_nodes_alive=2
        self.set_node_list=0
        self.sender_node_list=[]
        self.process_nodes_list=[]
        self.input_node_list=[]
        self.central_manager_list=[]
        self.output_node_list=[]
        self.exclude_nodes=0
        self.exclude_sender_nodes=[]
        self.exclude_process_nodes=[]
        self.exclude_input_nodes=[]
        self.exclude_central_manager=[]
        self.exclude_output_nodes=[]
        self.use_infiniband = 1
        self.path = ""
        self.desc_size = 19
        self.data_size = 27
        self.activate_timesliceforwarding = 0
        self.write_data_to_file = 0
        self.path_to_output_file = ""
        self.analyze_data = 0
        self.port = 0
        self.use_dtsa_files = 0
        self.malloc_size = 1000000000
        self.ZIB_timesliceforwarding = 1
        self.num_components = 1
        self.num_central_manager = 1
        self.num_input_nodes = 1
        self.num_sender_per_node = 1
        self.num_output_nodes = 1
        self.input_tsa_files = []
        self.default_path = ""
        self.default_data_size = 0
        self.show_total_data = 0
        self.enable_graph = 0
        self.enable_progress_bar = 0
        self.show_only_entry_nodes = 0
        self.use_grafana = 0
        self.influx_node_ip = ""
        self.influx_token = ""
        self.use_flescluster = 0
        self.is_flescluster = 0
        self.cm_ip = ""
        self.central_manager_on_flescluster = 0
        self.sender_nodes_on_central_manager_node = 0
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
        self.get_mode()
        self.get_kill_par()
        self.get_node_list_par()
        self.get_flesnet_par()
        self.get_shm_commands()
        self.get_tsclient_par()
        self.get_ts_forwarding_par()
        self.get_mon_par()
        self.get_influx_par()

    def get_num_nodes_par(self):
        self.num_receivers = self.get_value('Number_of_Nodes', 'receiver_nodes','int',required=True)
        self.num_central_manager = self.get_value('Number_of_Nodes', 'central_manager', 'int', True)
        self.num_input_nodes = self.get_value('Number_of_Nodes', 'input_nodes', 'int', True)
        self.num_sender_per_node = self.get_value('Number_of_Nodes', 'num_sender_per_node','int',False)
        self.num_output_nodes = self.get_value('Number_of_Nodes', 'output_nodes','int',True)
        
    def get_general_par(self):
        self.use_collectl = self.get_value('general', 'use_collectl','int',required=True)
        self.num_cpus = self.get_value('general', 'num_cpus', 'int', required=False)
        self.mem = self.get_value('general', 'mem', 'str', required=False)
        self.loglevel = self.get_value('general','loglevel','str',required=True)
        self.check_log_lvl()
        
    def get_mode(self):
        self.activate_timesliceforwarding = self.get_value('mode', 'GSI_Timesliceforwarding','int', True)
        self.ZIB_timesliceforwarding = self.get_value('mode', 'ZIB_Timesliceforwarding','int',True)
        self.use_flescluster = self.get_value('mode', 'use_flescluster','int',required=True)
        self.is_flescluster = self.get_value('mode','is_flescluster','int',required=True)
        self.cm_ip = self.get_value('mode', 'cm_ip', 'str',required=False)
        self.central_manager_on_flescluster = self.get_value('mode','central_manager_on_flescluster','int',required=True)
        self.sender_nodes_on_central_manager_node = self.get_value('mode','sender_nodes_on_central_manager_node','int',required=True)

    def get_kill_par(self):
        self.activate_robustness_test = self.get_value('robustness_test','activate_robustness_test','int', self.activate_robustness_test, required=True)
        self.timer_for_kills = self.get_value('robustness_test', 'time_for_kills','time',self.timer_for_kills, required=False)
        self.num_min_sender_nodes_alive = self.get_value('robustness_test','num_min_sender_nodes_alive','int', self.num_min_sender_nodes_alive, required=False)
        self.num_min_process_nodes_alive = self.get_value('robustness_test','num_min_process_nodes_alive','int', self.num_min_process_nodes_alive, required=False)
        self.num_min_input_nodes_alive = self.get_value('robustness_test','num_min_input_nodes_alive','int', self.num_min_input_nodes_alive, required=False)
        self.num_min_central_manager_alive = self.get_value('robustness_test', 'num_min_central_manager_alive','int', self.num_min_central_manager_alive, required=False)
        self.num_min_output_nodes_alive = self.get_value('robustness_test','num_min_output_nodes_alive','int', self.num_min_output_nodes_alive, required=False)

    def get_node_list_par(self):
        self.set_node_list = self.get_value('set_node_list', 'set_node_list', 'int',self.set_node_list, False)
        self.sender_node_list = list(set(self.get_node_list('set_node_list','sender_nodes_list',self.sender_node_list,False)))
        self.process_nodes_list = list(set(self.get_node_list('set_node_list', 'process_nodes_list', self.process_nodes_list, False)))
        self.input_node_list = list(set(self.get_node_list('set_node_list','input_node_list',self.input_node_list,False)))
        self.central_manager_list = list(set(self.get_node_list('set_node_list','central_manager_node_list',self.central_manager_list,False)))
        self.output_node_list = list(set(self.get_node_list('set_node_list','output_node_list',self.output_node_list,False)))
        self.exclude_nodes = self.get_value('set_node_list','exclude_nodes','int', self.exclude_nodes,False)
        if self.exclude_nodes == 1:
            self.exclude_sender_nodes = self.get_node_list('set_node_list', 'exclude_sender_nodes', self.exclude_sender_nodes, False)
            self.exclude_process_nodes = self.get_node_list('set_node_list', 'exclude_process_nodes', self.exclude_process_nodes, False)
            self.exclude_input_nodes = self.get_node_list('set_node_list','exclude_input_nodes',self.exclude_input_nodes,False)
            self.exclude_central_manager = self.get_node_list('set_node_list','exclude_central_manager',self.exclude_central_manager,False)
            self.exclude_output_nodes = self.get_node_list('set_node_list','exclude_output_nodes',self.exclude_output_nodes,False)

            
    def get_flesnet_par(self):
        self.path = self.get_value('flesnet_commands', 'path_to_flesnet', 'str', required=True)
        self.use_infiniband = self.get_value('flesnet_commands','use_infiniband','int', self.use_infiniband, False)
        
    def get_shm_commands(self):
        self.desc_size = self.get_value('shm_commands','desc_size','int',self.desc_size,False)
        self.data_size = self.get_value('shm_commands','data_size','int', self.data_size, False)
        self.num_components = self.get_value('shm_commands', 'num_components','int',self.num_components,False)
    
    def get_tsclient_par(self):
        self.write_data_to_file = self.get_value('tsclient_commands', 'write_data_to_file', 'int', self.write_data_to_file, False)
        self.path_to_output_file = self.get_value('tsclient_commands', "path_to_output_file",'str', self.path_to_output_file, False)
        self.analyze_data = self.get_value('tsclient_commands', 'analyze_data', 'str', self.analyze_data, False)
        self.use_dtsa_files = self.get_value('tsclient_commands','use_dtsa_files','int',self.use_dtsa_files, False)
        self.malloc_size = self.get_value('tsclient_commands', 'malloc_size', 'int', self.malloc_size, False)        
        self.port = self.get_value('tsclient_commands', 'port', 'str', self.port, False)
        
    def get_ts_forwarding_par(self):
        self.input_tsa_files = self.get_input_file_list('ts_input_files')
        self.default_path = self.get_value('ts_input_files','i_default','str',required=True)
        self.default_data_size = self.get_value('ts_input_files','i_default_data',0,False)
        
        
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
        

    def get_input_file_list(self, section):
        file_groups = {}
    
        for entry in self.config[section]:
            # Match entries like input_node_0_1
            match = re.match(r'^(.*)_(\d+)$', entry)
    
            if match:
                base_name = match.group(1)
                index = int(match.group(2))
    
                path = self.config[section][entry]
                data_size_name = entry + '_data'
    
                if self.config.has_option(section, data_size_name):
                    data_size = self.config.getint(section, data_size_name)
                    value = (index, path, data_size)
                else:
                    value = (index, path)
    
                file_groups.setdefault(base_name, []).append(value)
    
        return list(file_groups.items())        

    def get_input_file_list_v2(self,section):
        file_list = []
        
        for entry in self.config[section]:
            if '_data' not in entry:
                path = self.config[section][entry]
                data_size_name = entry + '_data'
                if self.config.has_option(section, data_size_name):
                    data_size = self.config.getint(section, data_size_name)
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
            
    def get_node_list_V2(self,section,param, var=None, required=False):
         node_str = os.getenv(param)
         node_list = []
         if node_str is None:
             if self.config.has_option(section, param):
                 node_str = self.config.get(section,param)
             elif required:
                 logger.critical(f'required Param not set: {param}')
                 sys.exit(1)
             else:
                 logger.warning(f'not required Param not set: {param}')
                 return var
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

    
    def get_node_list(self, section, param, var=None, required=False):
        node_str = os.getenv(param)
    
        if node_str is None:
            if self.config.has_option(section, param):
                node_str = self.config.get(section, param)
            elif required:
                logger.critical(f"required Param not set: {param}")
                sys.exit(1)
            else:
                logger.warning(f"not required Param not set: {param}")
                return var
    
        node_list = []
    
        # Matches:
        # htc-cmp[001-004]
        # htc-cmp[001,005,010]
        # ccexe0001
        #
        # Also supports multiple groups:
        # htc-cmp[001-004],ccexe0001
        parts = re.findall(r'([a-zA-Z0-9\-]+)(?:\[(.*?)\]|(\d+))', node_str)
    
        for prefix, bracket_content, single_number in parts:
    
            # Case:
            # ccexe0001
            if single_number:
                node_list.append(f"{prefix}{single_number}")
                continue
    
            # Cases inside brackets
            # 001-004
            # 001,005,010
            for item in bracket_content.split(','):
    
                # Range
                if '-' in item:
                    start, end = item.split('-')
    
                    width = max(len(start), len(end))
                    start, end = int(start), int(end)
    
                    for i in range(start, end + 1):
    
                        # Optional special rule
                        if prefix == "ccexe" and i > 369:
                            continue
    
                        node_list.append(f"{prefix}{i:0{width}d}")
    
                # Single item
                else:
                    width = len(item)
                    i = int(item)
    
                    if prefix == "ccexe" and i > 369:
                        continue
    
                    node_list.append(f"{prefix}{i:0{width}d}")
    
        return sorted(set(node_list))
    
    def check_log_lvl(self):
        if self.loglevel not in ["DEBUG","CRITICAL","ERROR","WARNING","INFO","SUCCESS", "STATUS"]:
            logger.critical("log level not defined")
            self.exit_program()
        

    def validation_params(self, system_check):
        Params_check = params_checker(self, system_check)
        #Params_check.check_validity_of_files()
        Params_check.check_program_exists()
        Params_check.check_mode()
        if self.set_node_list:
            Params_check.check_nodes_exist()
            Params_check.check_for_duplicates()
            
        if self.exclude_nodes:
            Params_check.check_excluded_nodes_in_node_list()
        if os.getenv('SLURM_JOB_NUM_NODES'):
            Params_check.check_num_nodes()
            if self.set_node_list:
                Params_check.check_req_nodes_alloc()
            if self.exclude_nodes:
                Params_check.check_excluded_nodes_alloc()
        if self.activate_robustness_test:
            Params_check.check_kill_par()
        Params_check.check_timeslice_forwarding()
        if self.use_grafana:
            Params_check.check_influxdb2_access()
        Params_check.check_shm_commands()
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
        
    def get_node_list_cluster_2(self):
        node_str = os.environ.get('SLURM_NODELIST')
        node_list = []
    
        if node_str is None:
            logger.critical(
                'SLURM_NODELIST is not set, maybe you forgot to allocate the nodes'
            )
            sys.exit(1)
    
        # Match:
        # htc-cmp[001-004]
        # htc-cmp[001,005,010]
        # ccexe0001
        parts = re.findall(r'([a-zA-Z\-]+)(?:\[(.*?)\]|(\d+))', node_str)
    
        for prefix, bracket_content, single_number in parts:
    
            if single_number:
                node_list.append(f"{prefix}{single_number}")
                continue
    
            for item in bracket_content.split(','):
                if '-' in item:
                    start, end = item.split('-')
    
                    width = max(len(start), len(end))
                    start, end = int(start), int(end)
    
                    for i in range(start, end + 1):
                        if prefix == "ccexe" and i > 369:
                            continue
    
                        node_list.append(f"{prefix}{i:0{width}d}")
    
                else:
                    i = int(item)
                    width = len(item)
    
                    if prefix == "ccexe" and i > 369:
                        continue
    
                    node_list.append(f"{prefix}{i:0{width}d}")
    
        return sorted(set(node_list))
    
    def get_node_list_cluster(self):
        node_str = os.environ.get("SLURM_NODELIST")
        node_list = []
    
        if node_str is None:
            logger.critical(
                "SLURM_NODELIST is not set, maybe you forgot to allocate the nodes"
            )
            sys.exit(1)
    
        # Matches:
        # htc-cmp[001-004]
        # htc-cmp[001,005,010]
        # ccexe0001
        # en[01-16]
        # en01
        # node[1-8]
        # node01
        parts = re.findall(r"([a-zA-Z\-]+)(?:\[(.*?)\]|(\d+))", node_str)
    
        for prefix, bracket_content, single_number in parts:
    
            if single_number:
                node_list.append(f"{prefix}{single_number}")
                continue
    
            for item in bracket_content.split(","):
                if "-" in item:
                    start, end = item.split("-")
    
                    width = max(len(start), len(end))
                    start, end = int(start), int(end)
    
                    for i in range(start, end + 1):
                        node_list.append(f"{prefix}{i:0{width}d}")
    
                else:
                    i = int(item)
                    width = len(item)
                    node_list.append(f"{prefix}{i:0{width}d}")
    
        return sorted(set(node_list))
    
    
    def check_validity_of_files(self):
        logger.debug('check if the input files exist')
        if not self.Par_.input_tsa_files:
            logger.critical('no .tsa input file for the tsclient to read from')
            self.exit_program()
        else:
            for elem in self.Par_.input_tsa_files:
                pattern = elem[1]
                matches = glob.glob(pattern)
            
                if not matches:
                    logger.critical(f'No files match pattern: {pattern}')
                    self.exit_program()
            
                # Optionally ensure all matches are files
                for match in matches:
                    if not os.path.isfile(match):
                        logger.critical(f'{match} is not a file')
                        self.exit_program()
                        
                        
    def check_program_exists(self):
        logger.debug('check if the path to flesnet is correct')
        for program in ['./mstool', './tsclient', './timeslice_forwarder']:
            program_path = self.Par_.path + program
            if not (os.path.isfile(program_path) and os.access(program_path, os.X_OK)):
                logger.critical(f'Program {program} does not exist')
                self.exit_program()
                
    def check_mode(self):
        logger.debug('checking the mode')
        if not self.Par_.activate_timesliceforwarding and not self.Par_.ZIB_timesliceforwarding:
            logger.critical("no active mode. Nothing will happen when executing the program")
            self.exit_program()
        if self.Par_.activate_timesliceforwarding and self.Par_.ZIB_timesliceforwarding:
            logger.critical("Two different timesliceforwardings are active.")
            self.exit_program()

    def check_for_duplicates(self):
        if self.Par_.activate_timesliceforwarding:
            for sender_node in self.Par_.sender_node_list:
                if sender_node in self.Par_.process_nodes_list:
                    logger.critical(f'sender node: {sender_node} is also an receiver node. This is not allowed')
        if self.Par_.ZIB_timesliceforwarding:
            use_input_nodes = (not self.Par_.use_flescluster or (self.Par_.use_flescluster and self.Par_.is_flescluster))
            use_output_nodes = not self.Par_.use_flescluster or (self.Par_.use_flescluster and not self.Par_.is_flescluster)
            if self.Par_.use_input_nodes:
                for input_node in self.Par_.input_node_list:
                    if input_node in self.Par_.output_node_list:
                        logger.critical(f'input node: {input_node} is also an output node. This is not allowed')
                        self.exit_program()
                    if input_node in self.Par_.central_manager_list:
                        logger.critical(f'input node: {input_node} is also a central manager. This is not allowed')
                        self.exit_program()
            if self.Par_.use_output_nodes:
                for central_manager in self.Par_.central_manager_list:
                    if central_manager in self.Par_.output_node_list:
                        logger.critical(f'central manager: {central_manager} is also an output node. This is not allowed')
                        self.exit_program()
                        
    def check_num_nodes(self):
        logger.debug('check the number of nodes')
        num_tot_nodes_req = 0
        num_nodes_req_list = 0
        if self.Par_.activate_timesliceforwarding:
            num_tot_nodes_req += 2*self.Par_.num_receivers
            if self.Par_.set_node_list:
                num_nodes_req_list += len(self.Par_.process_nodes_list) + len(self.Par_.sender_node_list)
        elif self.Par_.ZIB_timesliceforwarding:
            use_input_nodes = (not self.Par_.use_flescluster or (self.Par_.use_flescluster and self.Par_.is_flescluster))
            use_output_nodes = not self.Par_.use_flescluster or (self.Par_.use_flescluster and not self.Par_.is_flescluster)
            if use_output_nodes:
                num_tot_nodes_req += self.Par_.num_central_manager + self.Par_.num_output_nodes
                if self.Par_.set_node_list:
                    num_nodes_req_list += len(set(self.Par_.output_node_list + self.Par_.central_manager_list))
            if use_input_nodes:
                num_tot_nodes_req += self.Par_.num_input_nodes
                if self.Par_.set_node_list:
                    num_nodes_req_list += len((self.Par_.input_node_list))
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
        logger.debug('check if all nodes that are wished actually exist')
        try:
            cmd = ["sinfo", "-N", "-h", "-o", "%N %f"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"[!] Error running sinfo: {e} Cannot check the validity of the given nodelist")
        node_features = {}
        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            parts = line.strip().split(None, 1)
            node = parts[0]
            features = parts[1] if len(parts) > 1 else ""
            node_features[node] = features 
        req_node_list = []
        if self.Par_.activate_timesliceforwarding:
            req_node_list += [("Sender node", node) for node in self.Par_.sender_node_list]
            req_node_list += [("Process node", node) for node in self.Par_.process_nodes_list]
        elif self.Par_.ZIB_timesliceforwarding:
            use_input_nodes = (not self.Par_.use_flescluster or (self.Par_.use_flescluster and self.Par_.is_flescluster))
            use_output_nodes = not self.Par_.use_flescluster or (self.Par_.use_flescluster and not self.Par_.is_flescluster)
            if use_input_nodes:
                req_node_list += [("Input node", node) for node in self.Par_.input_node_list]
            if use_output_nodes:
                req_node_list += [("Central manager", node) for node in self.Par_.central_manager_list]
                req_node_list += [("Output node", node) for node in self.Par_.output_node_list]
        for node_type,node in req_node_list:
            if node not in node_features:
                logger.critical(f"{node_type}: {node} not found on the cluster")
                self.exit_program()
                continue
            if self.Par_.use_infiniband and not self.Par_.use_flescluster:
                features = node_features[node]
                if "infiniband" not in features.lower():
                    logger.critical(f"{node_type}: {node} does not provide Infiniband")
                    self.exit_program()


    def check_req_nodes_alloc(self):
        logger.debug('check if all nodes that are wished via the list are allocated')
        node_list = self.get_node_list_cluster()
        req_node_list = []
        req_node_list += [("Entry node", node) for node in self.Par_.entry_nodes_list]
        req_node_list += [("Build node", node) for node in self.Par_.build_nodes_list]
        if self.Par_.activate_timesliceforwarding:
            if self.Par_.use_flesnet:
                req_node_list += [("Sender node", node) for node in self.Par_.sender_node_list]
            req_node_list += [("Process node", node) for node in self.Par_.process_nodes_list]
        elif self.Par_.ZIB_timesliceforwarding:
            use_input_nodes = not self.Par_.use_flesnet and (not self.Par_.use_flescluster or (self.Par_.use_flescluster and self.Par_.is_flescluster))
            use_output_nodes = not self.Par_.use_flescluster or (self.Par_.use_flescluster and not self.Par_.is_flescluster)
            if use_input_nodes:
                req_node_list += [("Input node", node) for node in self.Par_.input_node_list]
            if use_output_nodes:
                req_node_list += [("Central manager", node) for node in self.Par_.central_manager_list]
                req_node_list += [("Output node", node) for node in self.Par_.output_node_list]
        for node_type,node in req_node_list:
            if node not in node_list:
                logger.critical(f"required {node_type}: {node} not allocated")
                self.exit_program()
                        
                
                
    def check_excluded_nodes_alloc(self):
        logger.debug('check if excluded nodes are allocated')
        node_list = self.get_node_list_cluster()
        excluded_node_list = []
        excluded_node_list += [("Entry node",node) for node in self.Par_.exclude_entry_nodes]
        excluded_node_list += [("Build node",node) for node in self.Par_.exclude_build_nodes]
        if self.Par_.activate_timesliceforwarding:
            excluded_node_list += [("Process node",node) for node in self.Par_.exclude_process_nodes]
            excluded_node_list += [("Sender node", node) for node in self.Par_.exclude_sender_nodes]
        if self.Par_.ZIB_timesliceforwarding:
            use_input_nodes = not self.Par_.use_flesnet and (not self.Par_.use_flescluster or (self.Par_.use_flescluster and self.Par_.is_flescluster))
            use_output_nodes = not self.Par_.use_flescluster or (self.Par_.use_flescluster and not self.Par_.is_flescluster)
            if use_input_nodes:
                excluded_node_list += [("Input node",node) for node in self.Par_.exclude_input_nodes]
            if use_output_nodes:
                excluded_node_list += [("Central Manager",node) for node in self.Par_.exclude_central_manager]
                excluded_node_list += [("Output node",node) for node in self.Par_.exclude_output_nodes]
        for node_type,node in excluded_node_list:
            if node in node_list:
                logger.warning(f"Excluded {node_type}: {node} is allocated. It will not be used as an {node_type}")
                
    #TODO
    def check_excluded_nodes_in_node_list(self):
        logger.debug('check if excluded nodes are wished')
        excluded_node_list = []
        use_input_nodes = (not self.Par_.use_flescluster or (self.Par_.use_flescluster and self.Par_.is_flescluster))
        use_output_nodes = not self.Par_.use_flescluster or (self.Par_.use_flescluster and not self.Par_.is_flescluster)
        if self.Par_.activate_timesliceforwarding:
            excluded_node_list += [("Process node",node) for node in self.Par_.exclude_process_nodes]
            excluded_node_list += [("Sender node", node) for node in self.Par_.exclude_sender_nodes]
        if self.Par_.ZIB_timesliceforwarding:

            if use_input_nodes:
                excluded_node_list += [("Input node",node) for node in self.Par_.exclude_input_nodes]
            if use_output_nodes:
                excluded_node_list += [("Central Manager",node) for node in self.Par_.exclude_central_manager]
                excluded_node_list += [("Output node",node) for node in self.Par_.exclude_output_nodes]
        if os.getenv('SLURM_JOB_NUM_NODES') and self.Par_.set_node_list:
            req_node_list = []
            if self.Par_.activate_timesliceforwarding:
                req_node_list += self.Par_.process_nodes_list
            if self.Par_.ZIB_timesliceforwarding:
                if use_input_nodes:
                    req_node_list += self.Par_.input_node_list
                if use_output_nodes:
                    req_node_list += self.Par_.central_manager_list
                    req_node_list += self.Par_.output_node_list
            for node_type,node in excluded_node_list:
                if node in req_node_list:
                    logger.critical(f"excluded {node_type}: {node} is both excluded and explicitly set to allocate. This will lead to a conflict when trying to alloacate the nodes")
                    self.exit_program()
        if self.Par_.set_node_list:
            if self.Par_.activate_timesliceforwarding:
                for excluded_process in self.Par_.exclude_process_nodes:
                    if excluded_process in self.Par_.process_nodes_list:
                        logger.warning(f'excluded process node: {excluded_process} is both excluded and wished. So it is not used as an process node.')
            if self.Par_.ZIB_timesliceforwarding:
                if use_input_nodes:
                    for excluded_input in self.Par_.exclude_input_nodes:
                        if excluded_input in self.Par_.input_node_list:
                            logger.warning(f'excluded input node: {excluded_input} is both excluded and wished. So it is not used as an input node.')
                if use_output_nodes:
                    for excluded_cm in self.Par_.exclude_central_manager:
                        if excluded_cm in self.Par_.central_manager_list:
                            logger.warning(f'excluded Central Manager: {excluded_cm} is both excluded and wished. So it is not used as a Central Manager.')
                    for excluded_output in self.Par_.exclude_output_nodes:
                        if excluded_output in self.Par_.output_node_list:
                            logger.warning(f'excluded output node: {excluded_output} is both excluded and wished. So it is not used as an output node.')


    def check_kill_par(self):
        logger.debug('check robustness test V2')
        use_input_nodes = (not self.Par_.use_flescluster or (self.Par_.use_flescluster and self.Par_.is_flescluster))
        use_output_nodes = not self.Par_.use_flescluster or (self.Par_.use_flescluster and not self.Par_.is_flescluster)
        if self.Par_.timer_for_kills == timedelta(seconds=0):
            logger.critical("Cannot kill programs immediatly")
            self.exit_program()
                
            if self.Par_.num_min_build_nodes_alive > self.Par_.num_buildnodes:
                logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_build_nodes_alive} outmatches the total number of build nodes: {self.Par_.num_buildnodes}')
                self.exit_program()
        if self.Par_.activate_timesliceforwarding:
       
        
            if self.Par_.num_min_sender_nodes_alive > self.Par_.num_receivers:
                logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_sender_nodes_alive} outmatches the total number of sender nodes: {self.Par_.num_receivers}')
                self.exit_program()
            
            if self.Par_.num_min_process_nodes_alive > self.Par_.num_receivers:
                logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_process_nodes_alive} outmatches the total number of receiver nodes: {self.Par_.num_receivers}')
                self.exit_program()
        if self.Par_.ZIB_timesliceforwarding:
            if use_input_nodes:
                if self.Par_.num_min_input_nodes_alive > self.Par_.num_input_nodes:
                    logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_input_nodes_alive} outmatches the total number of input nodes: {self.Par_.num_input_nodes}')
                    self.exit_program()
            if use_output_nodes:
                if self.Par_.num_min_central_manager_alive > self.Par_.num_central_manager:
                    logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_central_manager_alive} outmatches the total number of central manager nodes: {self.Par_.num_central_manager}')
                    self.exit_program()
                    
                if self.Par_.num_min_output_nodes_alive > self.Par_.num_output_nodes:
                    logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_output_nodes_alive} outmatches the total number of output nodes: {self.Par_.num_output_nodes}')
                    self.exit_program()
        #TODO: make Param mem
    def check_shm_commands(self):
        logger.debug('check shm params')
        def exp_to_gib(exp: int) -> float:
            bytes_size = 2 ** exp
            gib = bytes_size / (2 ** 30)
            return gib
        
        if exp_to_gib(self.Par_.desc_size) >= 16:
            logger.critical(f'desc size is too big: {self.Par_.desc_size} would create a shm of size: {exp_to_gib(self.Par_.desc_size)} GB')
            self.exit_program()
        if exp_to_gib(self.Par_.data_size) >= 16:
            logger.critical(f'data size is too big: {self.Par_.data_size} would create a shm of size: {exp_to_gib(self.Par_.data_size)} GB')
    
    def check_timeslice_forwarding(self):
        logger.debug('check for timesliceforwarding params')
        if self.Par_.activate_timesliceforwarding == 1 or self.Par_.ZIB_timesliceforwarding == 1:
            if int(self.Par_.port) < 1023:
                logger.critical(f"used port for timeslice-forwarding: {self.Par_.port} is privileged, thus cannot be used")
                self.exit_program()
            if self.Par_.write_data_to_file == 1 and not os.path.exists(f"{self.Par_.path_to_output_file}"):
                logger.critical(f"output file path: {self.Par_.path_to_output_file} does not exists")
                self.exit_program()
                
    def check_influxdb2_access(self):
        logger.debug('check influxdb access')
        url = f"http://{self.Par_.influx_node_ip}"
        try:
            with InfluxDBClient(url=url, token=self.Par_.influx_token, org="CBM") as client:
                buckets_api = client.buckets_api()
                buckets = buckets_api.find_buckets().buckets
                if self.Par_.activate_timesliceforwarding or self.Par_.ZIB_timesliceforwarding:
                    if not any(b.name == "tsclient_status" for b in buckets):
                        logger.critical("bucket tsclient_status not found in influxdb")
                    if self.Par_.ZIB_timesliceforwarding:
                        if not any(b.name == "timeslice_forwarder_state" for b in buckets):
                            logger.critical("bucket timeslice_forwarder_state not found in influxdb")
                    
        except ApiException as e:
            if e.status == 401:
                logger.critical("Influxdb token invalid")
                self.exit_program()
            else:
                logger.critical(f"Access to the influxdb failed:, {e.status}, {e.reason}")
