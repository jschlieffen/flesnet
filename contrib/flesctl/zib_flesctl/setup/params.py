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
        self.num_entrynodes = 0
        self.num_buildnodes = 0
        self.num_receivers = 0
        self.use_collectl = 0
        self.num_cpus = 2
        self.loglevel="DEBUG"
        self.kill_nodes = 0
        self.timer_for_kill = timedelta(minutes=1)
        self.num_entrynodes_kills = 1 
        self.num_buildnodes_kills = 1
        self.num_sendernodes_kills = 1
        self.num_processnodes_kills = 1
        self.num_inputnodes_kills = 1
        self.num_cm_kills = 1
        self.num_outputnodes_kills = 1
        self.revive_nodes=1
        self.set_kill_list = 0
        self.entry_node_kill_list = []
        self.build_node_kill_list = []
        self.sender_node_kill_list = []
        self.process_node_kill_list = []
        self.input_node_kill_list = []
        self.central_manager_kill_list = []
        self.output_node_kill_list = []
        self.activate_robustness_test_V2 = 1
        self.timer_for_kills_V2 = timedelta(minutes=1)
        self.num_min_entry_nodes_alive=2
        self.num_min_build_nodes_alive=2
        self.num_min_sender_nodes_alive=2
        self.num_min_process_nodes_alive=2
        self.num_min_input_nodes_alive=2
        self.num_min_central_manager_alive=2
        self.num_min_output_nodes_alive=2
        self.set_node_list=0
        self.entry_nodes_list=[]
        self.build_nodes_list=[]
        self.sender_node_list=[]
        self.process_nodes_list=[]
        self.input_node_list=[]
        self.central_manager_list=[]
        self.output_node_list=[]
        self.exclude_nodes=0
        self.exclude_entry_nodes=[]
        self.exclude_build_nodes=[]
        self.exclude_sender_nodes=[]
        self.exclude_process_nodes=[]
        self.exclude_input_nodes=[]
        self.exclude_central_manager=[]
        self.exclude_output_nodes=[]
        self.path = ""
        self.transport_method = ""
        self.use_infiniband = 1
        self.customize_string = "" 
        self.use_pattern_gen = 0
        self.use_dmsa_files = 0
        self.input_files = []
        self.mean = 124000
        self.size_var = 0
        self.pattern = 1
        self.overlap = 1
        self.desc_size = 19
        self.data_size = 27
        self.activate_timesliceforwarding = 0
        self.write_data_to_file = 0
        self.path_to_output_file = ""
        self.analyze_data = 0
        self.port = 0
        self.use_dtsa_files = 0
        self.ZIB_timesliceforwarding = 1
        self.use_flesnet = 1
        self.num_components = 1
        self.num_central_manager = 1
        self.num_input_nodes = 1
        self.num_output_nodes = 1
        self.input_tsa_files = []
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
        self.get_mode()
        self.get_kill_par()
        self.get_kill_par_V2()
        self.get_node_list_par()
        self.get_flesnet_par()
        self.get_mstool_par()
        self.get_pgen_commands()
        self.get_shm_commands()
        self.get_tsclient_par()
        self.get_GSI_timesliceforwarding_par()
        self.get_ts_forwarding_par()
        self.get_mon_par()
        self.get_influx_par()

    def get_num_nodes_par(self):
        self.num_entrynodes = self.get_value('Number_of_Nodes', 'entry_nodes', 'int', required=True)
        self.num_buildnodes = self.get_value('Number_of_Nodes', 'build_nodes', 'int', required=True)
        self.num_receivers = self.get_value('Number_of_Nodes', 'receiver_nodes','int',required=True)
        self.num_central_manager = self.get_value('Number_of_Nodes', 'central_manager', 'int', True)
        self.num_input_nodes = self.get_value('Number_of_Nodes', 'input_nodes', 'int', True)
        self.num_output_nodes = self.get_value('Number_of_Nodes', 'output_nodes','int',True)
        
    def get_general_par(self):
        self.use_collectl = self.get_value('general', 'use_collectl','int',required=True)
        self.num_cpus = self.get_value('general', 'num_cpus', 'int', required=False)
        self.loglevel = self.get_value('general','loglevel','str',required=True)
        self.check_log_lvl()
        self.overlap_usage_of_nodes = self.get_value('general', 'overlap_usage_of_nodes', 'int', self.overlap_usage_of_nodes, False)
        
    def get_mode(self):
        self.activate_timesliceforwarding = self.get_value('mode', 'GSI_Timesliceforwarding','int', True)
        self.ZIB_timesliceforwarding = self.get_value('mode', 'ZIB_Timesliceforwarding','int',True)
        self.use_flesnet = self.get_value('mode','use_flesnet' ,'int', True)
    
    def get_kill_par(self):
        self.kill_nodes = self.get_value('robustness_test', 'kill_nodes_during_execution', 'int',self.kill_nodes, required=False)
        self.timer_for_kill = self.get_value('robustness_test', 'timer_for_kills', 'time', self.timer_for_kill, required=False)
        self.num_entrynodes_kills = self.get_value('robustness_test', 'num_entry_nodes_kills', 'int' , self.num_entrynodes_kills, required=False)
        self.num_buildnodes_kills = self.get_value('robustness_test', 'num_build_nodes_kills', 'int' , self.num_buildnodes_kills, required=False)
        self.num_sendernodes_kills = self.get_value('robustness_test','num_sender_nodes_kills','int', self.num_sendernodes_kills, required=False)
        self.num_processnodes_kills = self.get_value('robustness_test', 'num_process_nodes_kills', 'int' , self.num_processnodes_kills, required=False)
        self.num_inputnodes_kills = self.get_value('robustness_test', 'num_input_nodes_kills','int',self.num_inputnodes_kills, required=False)
        self.num_cm_kills = self.get_value('robustness_test','num_central_manager_kills','int',self.num_cm_kills,required=False)
        self.num_outputnodes_kills = self.get_value('robustness_test','num_output_nodes_kills','int',self.num_outputnodes_kills,required=False)
        self.revive_nodes=self.get_value('robustness_test', 'revive_nodes', 'int' , self.revive_nodes, required=False)
        self.set_kill_list = self.get_value('robustness_test', 'set_kill_list', 'int' , self.set_kill_list, required=False)
        if self.set_kill_list:
            self.entry_node_kill_list = self.get_node_list('robustness_test', 'entry_node_kill_list', self.entry_node_kill_list, False)
            self.build_node_kill_list = self.get_node_list('robustness_test', 'build_node_kill_list', self.build_node_kill_list, False)
            self.sender_node_kill_list = self.get_node_list('robustness_test', 'sender_node_kill_list', self.sender_node_kill_list, False)
            self.process_node_kill_list = self.get_node_list('robustness_test', 'process_node_kill_list', self.process_node_kill_list, False)
            self.input_node_kill_list = self.get_node_list('robustness_test','input_node_kill_list', self.input_node_kill_list, False)
            self.central_manager_kill_list = self.get_node_list('robustness_test','central_manager_kill_list', self.central_manager_kill_list, False)
            self.output_node_kill_list = self.get_node_list('robustness_test','output_node_kill_list',self.output_node_kill_list,False)
    

    def get_kill_par_V2(self):
        self.activate_robustness_test_V2 = self.get_value('robustness_test_V2','activate_robustness_test_V2','int', self.activate_robustness_test_V2, required=True)
        self.timer_for_kills_V2 = self.get_value('robustness_test_V2', 'time_for_kills','time',self.timer_for_kills_V2, required=False)
        self.num_min_entry_nodes_alive = self.get_value('robustness_test_V2', 'num_min_entry_nodes_alive', 'int',self.num_min_entry_nodes_alive, required=False)
        self.num_min_build_nodes_alive = self.get_value('robustness_test_V2','num_min_build_nodes_alive','int',self.num_min_build_nodes_alive, required=False)
        self.num_min_sender_nodes_alive = self.get_value('robustness_test_V2','num_min_sender_nodes_alive','int', self.num_min_sender_nodes_alive, required=False)
        self.num_min_process_nodes_alive = self.get_value('robustness_test_V2','num_min_process_nodes_alive','int', self.num_min_process_nodes_alive, required=False)
        self.num_min_input_nodes_alive = self.get_value('robustness_test_V2','num_min_input_nodes_alive','int', self.num_min_input_nodes_alive, required=False)
        self.num_min_central_manager_alive = self.get_value('robustness_test_V2', 'num_min_central_manager_alive','int', self.num_min_central_manager_alive, required=False)
        self.num_min_output_nodes_alive = self.get_value('robustness_test_V2','num_min_output_nodes_alive','int', self.num_min_output_nodes_alive, required=False)

    def get_node_list_par(self):
        self.set_node_list = self.get_value('set_node_list', 'set_node_list', 'int',self.set_node_list, False)
        self.entry_nodes_list = list(set(self.get_node_list('set_node_list', 'entry_nodes_list', self.entry_nodes_list, False)))
        self.build_nodes_list = list(set(self.get_node_list('set_node_list', 'build_nodes_list', self.build_nodes_list, False)))
        self.sender_node_list = list(set(self.get_node_list('set_node_list','sender_nodes_list',self.sender_node_list,False)))
        self.process_nodes_list = list(set(self.get_node_list('set_node_list', 'process_nodes_list', self.process_nodes_list, False)))
        self.input_node_list = list(set(self.get_node_list('set_node_list','input_node_list',self.input_node_list,False)))
        self.central_manager_list = list(set(self.get_node_list('set_node_list','central_manager_node_list',self.central_manager_list,False)))
        self.output_node_list = list(set(self.get_node_list('set_node_list','output_node_list',self.output_node_list,False)))
        self.exclude_nodes = self.get_value('set_node_list','exclude_nodes','int', self.exclude_nodes,False)
        if self.exclude_nodes == 1:
            self.exclude_entry_nodes = self.get_node_list('set_node_list', 'exclude_entry_nodes', self.exclude_entry_nodes, False)
            self.exclude_build_nodes = self.get_node_list('set_node_list', 'exclude_build_nodes', self.exclude_build_nodes, False)
            self.exclude_sender_nodes = self.get_node_list('set_node_list', 'exclude_sender_nodes', self.exclude_sender_nodes, False)
            self.exclude_process_nodes = self.get_node_list('set_node_list', 'exclude_process_nodes', self.exclude_process_nodes, False)
            self.exclude_input_nodes = self.get_node_list('set_node_list','exclude_input_nodes',self.exclude_input_nodes,False)
            self.exclude_central_manager = self.get_node_list('set_node_list','exclude_central_manager',self.exclude_central_manager,False)
            self.exclude_output_nodes = self.get_node_list('set_node_list','exclude_output_nodes',self.exclude_output_nodes,False)

            
    def get_flesnet_par(self):
        self.path = self.get_value('flesnet_commands', 'path_to_flesnet', 'str', required=True)
        self.transport_method = self.get_value('flesnet_commands', 'transport_method', 'str', required=True)
        self.use_infiniband = self.get_value('flesnet_commands','use_infiniband','int', self.use_infiniband, False)
        self.customize_string = self.get_value('flesnet_commands', 'customize_string', 'str', True)
    
    def get_mstool_par(self):
        self.use_pattern_gen = self.get_value('mstool_commands', 'use_pattern_gen', 'int', self.use_pattern_gen, False)
        self.use_dmsa_files = self.get_value('mstool_commands', 'use_dmsa_files', 'int', self.use_dmsa_files, False)
        self.input_files = self.get_input_file_list('input_file')
    
    def get_pgen_commands(self):
        self.mean = self.get_value('pgen_commands','mean','int', self.mean, required=False)
        self.size_var = self.get_value('pgen_commands','size_var','int',self.size_var, False)
        self.pattern = self.get_value('pgen_commands', 'pattern', 'int', self.pattern,False)
        self.overlap = self.get_value('pgen_commands','overlap','int',self.overlap,False)
        
    def get_shm_commands(self):
        self.desc_size = self.get_value('shm_commands','desc_size','int',self.desc_size,False)
        self.data_size = self.get_value('shm_commands','data_size','int', self.data_size, False)
        self.num_components = self.get_value('shm_commands', 'num_components','int',self.num_components,False)
    
    def get_tsclient_par(self):
        self.write_data_to_file = self.get_value('tsclient_commands', 'write_data_to_file', 'int', self.write_data_to_file, False)
        self.path_to_output_file = self.get_value('tsclient_commands', "path_to_output_file",'str', self.path_to_output_file, False)
        self.analyze_data = self.get_value('tsclient_commands', 'analyze_data', 'str', self.analyze_data, False)
        self.use_dtsa_files = self.get_value('tsclient_commands','use_dtsa_files','int',self.use_dtsa_files, False)

        
    def get_GSI_timesliceforwarding_par(self):
        self.port = self.get_value('GSI_timesliceforwarding', 'port', 'str', self.port, False)
        
    def get_ts_forwarding_par(self):
        self.input_tsa_files = self.get_input_file_list('ts_input_files')
        
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
            
    def get_node_list(self,section,param, var=None, required=False):
        node_list = []
        node_str = os.getenv(param)
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

    def check_log_lvl(self):
        if self.loglevel not in ["DEBUG","CRITICAL","ERROR","WARNING","INFO","SUCCESS", "STATUS"]:
            logger.critical("log level not defined")
            self.exit_program()
        

    def validation_params(self, system_check):
        Params_check = params_checker(self, system_check)
        Params_check.check_validity_of_files()
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
        
        #Params_check.check_log_lvl()
        if self.kill_nodes:
            Params_check.check_kill_par()
        if self.activate_robustness_test_V2:
            Params_check.check_kill_par_V2()
        self.show_only_entry_nodes = Params_check.check_transport_method()
        self.enable_progress_bar = Params_check.monitoring_check()
        Params_check.check_timeslice_forwarding()
        if self.use_grafana:
            Params_check.check_influxdb2_access()
        if self.use_pattern_gen:
            Params_check.check_pgen_commands()
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
    
    def check_validity_of_files(self):
        logger.debug('check if the input files exist')
        if self.Par_.use_pattern_gen != 1:
            if not self.Par_.input_files:
                logger.critical('no input files and no usage of the pattern generator')
                self.exit_program()
            else:
                for elem in self.Par_.input_files:
                    if not os.path.isfile(elem[1]):
                        logger.critical(f'File {elem[1]} does not exist')
                        self.exit_program()
        if not self.Par_.use_flesnet:
            if not self.Par_.input_tsa_files:
                logger.critical('no .tsa input file for the tsclient to read from')
                self.exit_program()
            else:
                for elem in self.Par_.input_tsa_files:
                    matches = glob.glob(elem[1])
            
                    if not matches:
                        logger.critical(f'No files found for {elem[1]}')
                        self.exit_program()
                        
                        
    def check_program_exists(self):
        logger.debug('check if the path to flesnet is correct')
        for program in ['./mstool', './flesnet', './tsclient', './timeslice_forwarder','./archive_validator']:
            program_path = self.Par_.path + program
            if not (os.path.isfile(program_path) and os.access(program_path, os.X_OK)):
                logger.critical(f'Program {program} does not exist')
                self.exit_program()
                
    def check_mode(self):
        logger.debug('checking the mode')
        if not self.Par_.use_flesnet and not self.Par_.activate_timesliceforwarding and not self.Par_.ZIB_timesliceforwarding:
            logger.critical("no active mode. Nothing will happen when executing the program")
            self.exit_program()
        if self.Par_.activate_timesliceforwarding and self.Par_.ZIB_timesliceforwarding:
            logger.critical("Two different timesliceforwardings are active.")
            self.exit_program()

    def check_for_duplicates(self):
        if self.Par_.activate_timesliceforwarding:
            if self.Par_.use_flesnet:
                for receiver_node in self.Par_.process_nodes_list:
                    if receiver_node in self.Par_.entry_nodes_list:
                        logger.critical(f'receiving node: {receiver_node} is also an entry node. This is not allowed')
                        self.exit_program()
                    if receiver_node in self.Par_.build_nodes_list:
                        logger.critical(f'receiving node: {receiver_node} is also an build node. This is not allowed')
                        self.exit_program()
            else:
                for sender_node in self.Par_.sender_node_list:
                    if sender_node in self.Par_.process_nodes_list:
                        logger.critical(f'sender node: {sender_node} is also an receiver node. This is not allowed')
        if self.Par_.ZIB_timesliceforwarding:
            if not self.Par_.use_flesnet:
                for input_node in self.Par_.input_node_list:
                    if input_node in self.Par_.output_node_list:
                        logger.critical(f'input node: {input_node} is also an output node. This is not allowed')
                        self.exit_program()
                    if input_node in self.Par_.central_manager_list:
                        logger.critical(f'input node: {input_node} is also a central manager. This is not allowed')
                        self.exit_program()
            for central_manager in self.Par_.central_manager_list:
                if central_manager in self.Par_.entry_nodes_list and self.Par_.use_flesnet:
                    logger.critical(f'central manager: {central_manager} is also an entry node. This is not allowed')
                    self.exit_program()
                if central_manager in self.Par_.build_nodes_list and self.Par_.use_flesnet:
                    logger.critical(f'central manager: {central_manager} is also an build node. This is not allowed')
                    self.exit_program()
                if central_manager in self.Par_.output_node_list:
                    logger.critical(f'central manager: {central_manager} is also an output node. This is not allowed')
                    self.exit_program()
            for output_node in self.Par_.output_node_list:
                if output_node in self.Par_.entry_nodes_list and self.Par_.use_flesnet:
                    logger.critical(f'output node: {output_node} is also an entry node. This is not allowed')
                    self.exit_program()
                if output_node in self.Par_.build_nodes_list and self.Par_.use_flesnet:
                    logger.critical(f'output node: {output_node} is also an build node. This is not allowed')
                    self.exit_program()
        if not self.Par_.overlap_usage_of_nodes:
            for entry_node in self.Par_.entry_nodes_list:
                if entry_node in self.Par_.build_nodes_list:
                    logger.critical(f'entry node: {entry_node} is also a Build node, while the overlap usage of nodes is deactivated')
                    self.exit_program()
        
    def check_num_nodes(self):
        logger.debug('check the number of nodes')
        num_tot_nodes_req = 0
        num_nodes_req_list = 0
        if self.Par_.use_flesnet:
            if self.Par_.overlap_usage_of_nodes == 1:
                num_tot_nodes_req = max(self.Par_.num_buildnodes, self.Par_.num_entrynodes) 
    
                if self.Par_.set_node_list:
                    num_nodes_req_list = max(len(self.Par_.entry_nodes_list), len(self.Par_.build_nodes_list))
            else:
                num_tot_nodes_req = self.Par_.num_buildnodes + self.Par_.num_entrynodes
    
                if self.Par_.set_node_list:
                    num_nodes_req_list = len(set(self.Par_.entry_nodes_list  + self.Par_.build_nodes_list))
        if self.Par_.activate_timesliceforwarding and self.Par_.use_flesnet:
            num_tot_nodes_req += self.Par_.num_buildnodes
            if self.Par_.set_node_list:
                num_nodes_req_list += len(self.Par_.process_nodes_list)
        elif self.Par_.activate_timesliceforwarding:
            num_tot_nodes_req += 2*self.Par_.num_receivers
            if self.Par_.set_node_list:
                num_nodes_req_list += len(self.Par_.process_nodes_list) + len(self.Par_.sender_node_list)
        elif self.Par_.ZIB_timesliceforwarding:
            num_tot_nodes_req += self.Par_.num_central_manager + self.Par_.num_output_nodes
            if self.Par_.set_node_list:
                num_nodes_req_list += len(set(self.Par_.output_node_list + self.Par_.central_manager_list))
            if not self.Par_.use_flesnet:
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
        if self.Par_.use_flesnet:
            req_node_list += [("Entry node", node) for node in self.Par_.entry_nodes_list]
            req_node_list += [("Build node", node) for node in self.Par_.build_nodes_list]
        if self.Par_.activate_timesliceforwarding:
            if self.Par_.use_flesnet:
                req_node_list += [("Sender node", node) for node in self.Par_.sender_node_list]
            req_node_list += [("Process node", node) for node in self.Par_.process_nodes_list]
        elif self.Par_.ZIB_timesliceforwarding:
            if self.Par_.use_flesnet:
                req_node_list += [("Input node", node) for node in self.Par_.input_node_list]
            req_node_list += [("Central manager", node) for node in self.Par_.central_manager_list]
            req_node_list += [("Output node", node) for node in self.Par_.output_node_list]
        for node_type,node in req_node_list:
            if node not in node_features:
                logger.critical(f"{node_type}: {node} not found on the cluster")
                self.exit_program()
                continue
            if self.Par_.use_infiniband:
                features = node_features[node]
                if "infiniband" not in features.lower():
                    logger.critical(f"{node_type}: {node} does not provide Infiniband")
                    self.exit_program()


    def check_req_nodes_alloc(self):
        logger.debug('check if all nodes that are wished via the list are allocated')
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
        req_node_list = []
        if self.Par_.use_flesnet:
            req_node_list += [("Entry node", node) for node in self.Par_.entry_nodes_list]
            req_node_list += [("Build node", node) for node in self.Par_.build_nodes_list]
        if self.Par_.activate_timesliceforwarding:
            if self.Par_.use_flesnet:
                req_node_list += [("Sender node", node) for node in self.Par_.sender_node_list]
            req_node_list += [("Process node", node) for node in self.Par_.process_nodes_list]
        elif self.Par_.ZIB_timesliceforwarding:
            if self.Par_.use_flesnet:
                req_node_list += [("Input node", node) for node in self.Par_.input_node_list]
            req_node_list += [("Central manager", node) for node in self.Par_.central_manager_list]
            req_node_list += [("Output node", node) for node in self.Par_.output_node_list]
        for node_type,node in req_node_list:
            if node not in node_list:
                logger.critical(f"required {node_type}: {node} not allocated")
                self.exit_program()
                        
                
                
    def check_excluded_nodes_alloc(self):
        logger.debug('check if excluded nodes are allocated')
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
        excluded_node_list = []
        if self.Par_.use_flesnet:
            excluded_node_list += [("Entry node",node) for node in self.Par_.exclude_entry_nodes]
            excluded_node_list += [("Build node",node) for node in self.Par_.exclude_build_nodes]
        if self.Par_.activate_timesliceforwarding:
            excluded_node_list += [("Process node",node) for node in self.Par_.exclude_process_nodes]
            if self.Par_.use_flesnet:
                excluded_node_list += [("Sender node", node) for node in self.Par_.exclude_sender_nodes]
        if self.Par_.ZIB_timesliceforwarding:
            if self.Par_.use_flesnet:
                excluded_node_list += [("Input node",node) for node in self.Par_.exclude_input_nodes]
            excluded_node_list += [("Central Manager",node) for node in self.Par_.exclude_central_manager]
            excluded_node_list += [("Output node",node) for node in self.Par_.exclude_output_nodes]
        for node_type,node in excluded_node_list:
            if node in node_list:
                logger.warning(f"Excluded {node_type}: {node} is allocated. It will not be used as an {node_type}")
                
    #TODO
    def check_excluded_nodes_in_node_list(self):
        logger.debug('check if excluded nodes are wished')
        excluded_node_list = []
        if self.Par_.use_flesnet:
            excluded_node_list += [("Entry node",node) for node in self.Par_.exclude_entry_nodes]
            excluded_node_list += [("Build node",node) for node in self.Par_.exclude_build_nodes]
        if self.Par_.activate_timesliceforwarding:
            excluded_node_list += [("Process node",node) for node in self.Par_.exclude_process_nodes]
            if self.Par_.use_flesnet:
                excluded_node_list += [("Sender node", node) for node in self.Par_.exclude_sender_nodes]
        if self.Par_.ZIB_timesliceforwarding:
            if self.Par_.use_flesnet:
                excluded_node_list += [("Input node",node) for node in self.Par_.exclude_input_nodes]
            excluded_node_list += [("Central Manager",node) for node in self.Par_.exclude_central_manager]
            excluded_node_list += [("Output node",node) for node in self.Par_.exclude_output_nodes]
        if os.getenv('SLURM_JOB_NUM_NODES') and self.Par_.set_node_list:
            req_node_list = []
            if self.Par_.use_flesnet:
                req_node_list += self.Par_.entry_nodes_list
                req_node_list +=  self.Par_.build_nodes_list
            if self.Par_.activate_timesliceforwarding:
                req_node_list += self.Par_.process_nodes_list
            if self.Par_.ZIB_timesliceforwarding:
                req_node_list += self.Par_.input_node_list
                req_node_list += self.Par_.central_manager_list
                req_node_list += self.Par_.output_node_list
            for node_type,node in excluded_node_list:
                if node in req_node_list:
                    logger.critical(f"excluded {node_type}: {node} is both excluded and explicitly set to allocate. This will lead to a conflict when trying to alloacate the nodes")
                    self.exit_program()
        if self.Par_.set_node_list:
            if self.Par_.use_flesnet:
                for excluded_entry in self.Par_.exclude_entry_nodes:
                    if excluded_entry in self.Par_.entry_nodes_list:
                        logger.warning(f'excluded entry node: {excluded_entry} is both excluded and wished. So it is not used as an entry node.')
                for excluded_build in self.Par_.exclude_build_nodes:
                    if excluded_build in self.Par_.build_nodes_list:
                        logger.warning(f'excluded build node: {excluded_build} is both excluded and wished. So it is not used as an build node.')
            if self.Par_.activate_timesliceforwarding:
                for excluded_process in self.Par_.exclude_process_nodes:
                    if excluded_process in self.Par_.process_nodes_list:
                        logger.warning(f'excluded process node: {excluded_process} is both excluded and wished. So it is not used as an process node.')
            if self.Par_.ZIB_timesliceforwarding:
                for excluded_input in self.Par_.exclude_input_nodes:
                    if excluded_input in self.Par_.input_node_list:
                        logger.warning(f'excluded input node: {excluded_input} is both excluded and wished. So it is not used as an input node.')
                for excluded_cm in self.Par_.exclude_central_manager:
                    if excluded_cm in self.Par_.central_manager_list:
                        logger.warning(f'excluded Central Manager: {excluded_cm} is both excluded and wished. So it is not used as a Central Manager.')
                for excluded_output in self.Par_.exclude_output_nodes:
                    if excluded_output in self.Par_.output_node_list:
                        logger.warning(f'excluded output node: {excluded_output} is both excluded and wished. So it is not used as an output node.')



    #TODO: wenn flesnet aktiv input nodes == build nodes !!!
    def check_kill_par(self):
        logger.debug('check robustness test')
        if self.Par_.activate_robustness_test_V2:
            logger.critical(f'cannot do both modes for robustness check')
            self.exit_program()
        if self.Par_.timer_for_kill == timedelta(seconds=0):
            logger.critical("Cannot kill programs immediatly")
            self.exit_program()
        if self.Par_.use_flesnet:
            if self.Par_.num_entrynodes_kills > self.Par_.num_entrynodes:
                logger.critical(f"Too many entry node kills: num entry nodes total: {self.Par_.num_entrynodes}, entry node kills: {self.Par_.num_entrynodes_kills}")
                self.exit_program()
            if self.Par_.num_buildnodes_kills > self.Par_.num_buildnodes:
                logger.critical(f"Too many build node kills: num build nodes total: {self.Par_.num_buildnodes}, build node kills: {self.Par_.num_buildnodes_kills}")
                self.exit_program()
        if self.Par_.activate_timesliceforwarding:
            if self.Par_.use_flesnet:
                if self.Par_.num_processnodes_kills > self.Par_.num_buildnodes:
                    logger.critical(f"Too many process node kills: num process nodes total: {self.Par_.num_buildnodes}, process node kills: {self.Par_.num_processnodes_kills}")
                    self.exit_program()
            else:
                if self.Par_.num_sendernodes_kills > self.Par_.num_receivers:
                    logger.critical(f"Too many sender node kills: num sender nodes total: {self.Par_.num_receiver}, sender node kills: {self.Par_.num_sendernodes_kills}")
                    self.exit_program()
                if self.Par_.num_processnodes_kills > self.Par_.num_receivers:
                    logger.critical(f"Too many process node kills: num process nodes total: {self.Par_.num_receivers}, process node kills: {self.Par_.num_processnodes_kills}")
                    self.exit_program()
        elif self.Par_.ZIB_timesliceforwarding:
            if self.Par_.use_flesnet: 
                if self.Par_.num_inputnodes_kills > self.Par_.num_buildnodes:
                    logger.critical(f"Too many input node kills: num input nodes total: {self.Par_.num_buildnodes}, input node kills: {self.Par_.num_inputnodes_kills}")
                    self.exit_program()
            else:
                if self.Par_.num_inputnodes_kills > self.Par_.num_input_nodes:
                    logger.critical(f"Too many input node kills: num input nodes total: {self.Par_.num_input_nodes}, input node kills: {self.Par_.num_inputnodes_kills}")
                    self.exit_program()
            if self.Par_.num_cm_kills > self.Par_.num_central_manager:
                logger.critical(f"Too many Central manager kills: num Central Manager total: {self.Par_.num_central_manager}, Central manager kills: {self.Par_.num_cm_kills}")
                self.exit_program()
            if self.Par_.num_outputnodes_kills > self.Par_.num_output_nodes:
                logger.critical(f"Too many output node kills: num output nodes total: {self.Par_.num_output_nodes}, output node kills: {self.Par_.num_outputnodes_kills}")
                self.exit_program()
        if self.Par_.set_kill_list:
            if not self.Par_.set_node_list:
                logger.critical("Node list is not set, but kill list. Might happen that nodes are gonna be killed that are not part of the allocation")
                self.exit_program()
            if self.Par_.use_flesnet:
                for kill_entry in self.Par_.entry_node_kill_list:
                    if kill_entry not in self.Par_.entry_nodes_list:
                        logger.critical(f"Supposed to kill entry node: {kill_entry}. But this is not contained in the entry nodes list")
                        self.exit_program()
                for kill_build in self.Par_.build_node_kill_list:
                    if kill_build not in self.Par_.build_nodes_list:
                        logger.critical(f"Supposed to kill build node: {kill_build}. But this is not contained in the build nodes list")
                        self.exit_program()
            if self.Par_.activate_timesliceforwarding:
                for kill_process in self.Par_.sender_node_kill_list:
                    if kill_process not in self.Par_.sender_node_list:
                        logger.critical(f"Supposed to kill sender node: {kill_process}. But this is not contained in the sender nodes list")
                        self.exit_program()
                for kill_process in self.Par_.process_node_kill_list:
                    if kill_process not in self.Par_.process_nodes_list:
                        logger.critical(f"Supposed to kill process node: {kill_process}. But this is not contained in the process nodes list")
                        self.exit_program()
            if self.Par_.ZIB_timesliceforwarding:
                for kill_input in self.Par_.input_node_kill_list:
                    if kill_input not in self.Par_.input_node_list:
                        logger.critical(f"Supposed to kill input node: {kill_input}. But this is not contained in the input nodes list")
                        self.exit_program()
                for kill_cm in self.Par_.central_manager_kill_list:
                    if kill_cm not in self.Par_.central_manager_list:
                        logger.critical(f"Supposed to kill Central Manager: {kill_cm}. But this is not contained in the Central Manager list")
                        self.exit_program()
                for kill_output in self.Par_.input_node_kill_list:
                    if kill_output not in self.Par_.output_node_list:
                        logger.critical(f"Supposed to kill output node: {kill_output}. But this is not contained in the output nodes list")
                        self.exit_program()
    
    def check_kill_par_V2(self):
        logger.debug('check robustness test V2')
        if self.Par_.timer_for_kills_V2 == timedelta(seconds=0):
            logger.critical("Cannot kill programs immediatly")
            self.exit_program()
        if self.Par_.use_flesnet:
            if self.Par_.num_min_entry_nodes_alive >= self.Par_.num_entrynodes:
                logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_entry_nodes_alive} outmatches the total number of entry nodes: {self.Par_.num_entrynodes}')
                self.exit_program()
                
            if self.Par_.num_min_build_nodes_alive >= self.Par_.num_buildnodes:
                logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_build_nodes_alive} outmatches the total number of build nodes: {self.Par_.num_buildnodes}')
                self.exit_program()
        if self.Par_.activate_timesliceforwarding:
            if self.Par_.use_flesnet:
                if self.Par_.num_min_sender_nodes_alive >= self.Par_.num_buildnodes:
                    logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_sender_nodes_alive} outmatches the total number of sender nodes: {self.Par_.num_buildnodes}')
                    self.exit_program()
                
                if self.Par_.num_min_process_nodes_alive >= self.Par_.num_buildnodes:
                    logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_process_nodes_alive} outmatches the total number of receiver nodes: {self.Par_.num_buildnodes}')
                    self.exit_program()
            
            else:
                if self.Par_.num_min_sender_nodes_alive >= self.Par_.num_receivers:
                    logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_sender_nodes_alive} outmatches the total number of sender nodes: {self.Par_.num_receivers}')
                    self.exit_program()
                
                if self.Par_.num_min_process_nodes_alive >= self.Par_.num_receivers:
                    logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_process_nodes_alive} outmatches the total number of receiver nodes: {self.Par_.num_receivers}')
                    self.exit_program()
        if self.Par_.ZIB_timesliceforwarding:
            if self.Par_.use_flesnet:
                if self.Par_.num_min_input_nodes_alive >= self.Par_.num_buildnodes:
                    logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_input_nodes_alive} outmatches the total number of input nodes: {self.Par_.num_buildnodes}')
                    self.exit_program()
            else:
                if self.Par_.num_min_input_nodes_alive >= self.Par_.num_input_nodes:
                    logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_input_nodes_alive} outmatches the total number of input nodes: {self.Par_.num_input_nodes}')
                    self.exit_program()
            if self.Par_.num_min_central_manager_alive >= self.Par_.num_central_manager:
                logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_central_manager_alive} outmatches the total number of central manager nodes: {self.Par_.num_central_manager}')
                self.exit_program()
                
            if self.Par_.num_min_output_nodes_alive >= self.Par_.num_output_nodes:
                logger.critical(f'The number of minimal nodes that are supposed to let be online: {self.Par_.num_min_output_nodes_alive} outmatches the total number of output nodes: {self.Par_.num_output_nodes}')
                self.exit_program()
                
    def check_transport_method(self):
        logger.debug('check transport method')
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

    def check_pgen_commands(self):
        def exp_to_mib(exp: int) -> float:
            bytes_size = 2 ** exp
            mib = bytes_size / (2 ** 20)
            return mib
        logger.debug('check pgen params')
        match = re.search(r'--timeslice-size\s+(\d+)', self.Par_.customize_string)
        timeslice_size = int(match.group(1)) if match else None
        if timeslice_size is not None:
            if self.Par_.mean*timeslice_size >= 2**self.Par_.data_size:
                logger.critical(f'size of microslices are too large for the shm. Flesnet will not be able to transmit any data: \n'
                                f'mean: {self.Par_.mean} * timeslice-size: {timeslice_size} = {self.Par_.mean*timeslice_size/1000000} MB > shm data size: {exp_to_mib(self.Par_.data_size)} MB')
                self.exit_program()
        if self.Par_.pattern != 0 and self.Par_.pattern != 1:
            logger.critical(f'unknown value for pattern : {self.Par_.pattern}')
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
            
    def monitoring_check(self):
        logger.debug('check monitoring params')
        if self.Par_.enable_progress_bar == 1:
            if self.Par_.use_pattern_gen == 1:
                logger.warning('Pattern Generator is used, thus there is no limit for the total data. Therefore progress bar is disabled')
                return 0
            return 1
    
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
        url = f"http://{self.Par_.influx_node_ip}:8086"
        try:
            with InfluxDBClient(url=url, token=self.Par_.influx_token, org="CBM") as client:
                buckets_api = client.buckets_api()
                buckets = buckets_api.find_buckets().buckets
                if self.Par_.use_flesnet:
                    if not any(b.name == "flesnet_status" for b in buckets):
                        logger.critical("bucket flesnet_status not found in influxdb")
                        self.exit_program()
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
