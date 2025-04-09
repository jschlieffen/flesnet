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

# =============================================================================
# This file reads the params from the config file and checks the validation
# =============================================================================

class Params:
    
    # =============================================================================
    # Here are the default values of the params that are not necessarily required   
    # =============================================================================
    def __init__(self,config_file):
        self.entry_nodes = 0
        self.build_nodes = 0
        self.path = ""
        self.transport_method = ""
        self.customize_string = "" 
        self.use_pattern_gen = 0
        self.use_dmsa_files = 0
        self.input_file_list = []
        self.show_total_data = 0
        self.show_graph = 0
        self.show_progress_bar = 0
        self.show_only_entry_nodes = 0
        self.use_grafana = 0
        self.influx_node_ip = ""
        self.influx_token = ""
        self.overlap_usage_of_nodes = 0
        self.config = cfg.ConfigParser()
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
        self.entry_nodes = self.get_value('Number_of_Nodes', 'entry_nodes', 'int', True)
        self.build_nodes = self.get_value('Number_of_Nodes', 'build_nodes', 'int', True)
        self.path = self.get_value('flesnet_commands', 'path_to_flesnet', 'str', True)
        self.transport_method = self.get_value('flesnet_commands', 'transport_method', 'str', True)
        self.customize_string = self.get_value('flesnet_commands', 'customize_string', 'str', True)
        self.use_pattern_gen = self.get_value('mstool_commands', 'use_pattern_gen', 'int', self.use_pattern_gen, False)
        self.use_dmsa_files = self.get_value('mstool_commands', 'use_dmsa_files', 'int', self.use_dmsa_files, False)
        self.input_file_list = self.get_input_file_list('input_file')
        self.show_total_data = self.get_value('Monotoring', 'show_total_data', 'int', True)
        self.show_graph = self.get_value('Monotoring', 'show_graph', 'int', False)
        self.show_progress_bar = self.get_value('Monotoring', 'show_progress_bar', 'int', self.show_progress_bar, False)
        self.show_only_entry_nodes = self.get_value('Monotoring', 'show_only_entry_nodes', 'int', self.show_only_entry_nodes, False)
        self.overlap_usage_of_nodes = self.get_value('general', 'overlap_usage_of_nodes', 'int', self.overlap_usage_of_nodes, False)
        self.use_grafana = self.get_value('influxdb', 'use_grafana', 'int', True)
        self.influx_node_ip = self.get_value('influxdb', 'influx_node_ip','str', self.influx_node_ip, False)
        self.influx_token = self.get_value('influxdb', 'token','str', self.influx_token, False)

        
    
    def get_value(self, section, param, par_type, var=None, required=False):
        val = os.getenv(param)
        
        if val is not None:
            if par_type=='int':
                return int(val)
            return val
        elif self.config.has_option(section, param):
            if par_type == 'int':
                return self.config.getint(section, param)
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

    # =============================================================================
    # Checks the validation of certain parameters. Currently every validation has 
    # to be added by hand    
    # =============================================================================
    def validation_params(self):
        if not self.input_file_list:
            if self.use_pattern_gen == 0:
                logger.critical('no input files and no usage of the pattern generator')
                sys.exit(1)
        else:
            for elem in self.input_file_list:
                if not os.path.isfile(elem[1]):
                    logger.critical(f'File {elem[1]} does not exist')
                    sys.exit(1)
        for program in ['./mstool', './flesnet']:
            program_path = self.path + program
            if not (os.path.isfile(program_path) and os.access(program_path, os.X_OK)):
                logger.critical(f'Program {program} does not exist')
                sys.exit(1)
        if self.transport_method == 'zeromq' and self.show_only_entry_nodes == 0:
            logger.warning(f'transport method zeromq only shows data rate for the entry nodes. Therefore param show_only_entry_nodes is set to 1')
            self.show_only_entry_nodes = 1
        
        if self.show_progress_bar:
            if self.use_pattern_gen == 1:
                logger.warning('Pattern Generator is used, thus there is no limit for the total data. Therefore progress bar is disabled')
                self.show_progress_bar = 0
            for tup in self.input_file_list:
                if len(tup) == 2:
                    logger.warning(f'File for entry node {tup[0]} is not set. Requested for the progress bar. Therefore progress bar is disabled')
                    self.show_progress_bar = 0

# =============================================================================
# only for dev purpose
# =============================================================================
def main():
    Par_ = Params('config.cfg')
    Par_.validation_params()
    print('\n')
    print(Par_)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

if __name__ == '__main__':
    main()