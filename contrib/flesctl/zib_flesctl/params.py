#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 15:48:03 2025

@author: jschlieffen
"""

import configparser as cfg
import os
import sys


#TODO: check if vars are set correctly
class Params:
    
    def __init__(self,config_file):
        self.entry_nodes = 0
        self.build_nodes = 0
        self.path = ""
        self.transport_method = ""
        self.timeslice_size = 0
        self.processor_instances = 0
        self.tsclient_string = ""
        self.input_file_list = []
        self.show_total_data = 0
        self.use_grafana = 0
        self.influx_node_ip = ""
        self.influx_token = ""
        self.overlap_usage_of_nodes = 0
        self.config = cfg.ConfigParser()
        self.config.read(config_file)
        #self.config = config_file
        self.get_params(config_file)
        
    def __str__(self):
        attributes = ', '.join(f"{key}={value}" for key, value in self.__dict__.items())
        return f"{self.__class__.__name__}({attributes})"
    
    def get_params(self, config_file):
        #config = cfg.ConfigParser()
        #config.read(config_file)
        
        self.entry_nodes = self.get_value('Number_of_Nodes', 'entry_nodes', 'int', True)
        self.build_nodes = self.get_value('Number_of_Nodes', 'build_nodes', 'int', True)
        self.path = self.get_value('flesnet_commands', 'path_to_flesnet', 'str', True)
        self.transport_method = self.get_value('flesnet_commands', 'transport_method', 'str', True)
        self.customize_string = self.get_value('flesnet_commands', 'customize_string', 'str', True)
        self.input_file_list = [(param, value) for param, value in self.config.items('input_file')]
        self.show_total_data = self.get_value('Monotoring', 'show_total_data', 'int', True)
        self.overlap_usage_of_nodes = self.get_value('general', 'overlap_usage_of_nodes', 'int', False)
        self.use_grafana = self.get_value('influxdb', 'use_grafana', 'int', True)
        self.influx_node_ip = self.get_value('influxdb', 'influx_node_ip','str', False)
        self.influx_token = self.get_value('influxdb', 'token','str', False)
        #print(self.show_total_data)
    
    def get_value(self, section, param, par_type, required=False):
        val = os.getenv(param)
        #config = cfg.ConfigParser()
        #config.read(self.config_file)
        
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
            print('Error: Param not set: %s' % (param))
            sys.exit(1)
        else:
            return None


def main():
    Par_ = Params('config.cfg')
    print(Par_)

if __name__ == '__main__':
    main()