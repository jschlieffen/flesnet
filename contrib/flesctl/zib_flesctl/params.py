#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 17 15:48:03 2025

@author: jschlieffen
"""

import configparser as cfg

class Params:
    
    def __init__(self,config_file):
        self.entry_nodes = 0
        self.build_nodes = 0
        self.input_file_list = []
        self.show_total_data = 0
        self.influx_node_ip = ""
        self.influx_token = ""
        self.get_params(config_file)
        
    def __str__(self):
        attributes = ', '.join(f"{key}={value}" for key, value in self.__dict__.items())
        return f"{self.__class__.__name__}({attributes})"
    
    def get_params(self, config_file):
        config = cfg.ConfigParser()
        config.read(config_file)
        
        self.entry_nodes = config.getint('Number_of_Nodes', 'entry_nodes')
        self.build_nodes = config.getint('Number_of_Nodes', 'build_nodes')
        self.input_file_list = [(param, value) for param, value in config.items('input_file')]
        self.show_total_data = config.getint('Monotoring', 'show_total_data')
        self.influx_node_ip = config.get('influxdb', 'influx_node_ip')
        self.influx_token = config.get('influxdb', 'token')
    
def main():
    Par_ = Params('config.cfg')
    print(Par_)

if __name__ == '__main__':
    main()