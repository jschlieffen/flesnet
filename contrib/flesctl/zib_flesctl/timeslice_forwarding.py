#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed May 14 17:14:05 2025

#@author: jschlieffen

"""
Usage: timeslice_forwarding.py <logfile> <build_node_ip> <influx_node_ip> <influx_token> <use_grafana> <path> <port>

Arguments:
    
    <logfile> The Logfile to use
    <ip> The ip address to use
    <influx_node_ip> The ip of the where the influx container is runnning
    <influx_token> The token to the influx-db
    <use_grafana> enables/disables grafana
    <path> The path to tsclient
    <port> The port for the timeslice-forwarding
"""

import subprocess
import time
import docopt
import sys
import os


#may be extended
def calc_ip_str(ip,port):
    ip_string = f"tcp://{ip}:{port}"
    return ip_string

def main(ip,logfile,influx_node_ip, influx_token, use_grafana,path, port):
    ip_string = calc_ip_str(ip, port)
    
    grafana_string = ''
    if use_grafana:
        os.environ['CBM_INFLUX_TOKEN'] = influx_token
        grafana_string = '-m influx2:%s:8086:tsclient_status: ' % (influx_node_ip)
        
    tsclient_commands = (
            '%s./tsclient -l 1 -L %s -i %s -a %s > /dev/null 2>&1 &'
            % (path,logfile,ip_string, grafana_string)
        )
    result_tsclient = subprocess.Popen(tsclient_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    input_data = ''
    while input_data == '':
        input_data = sys.stdin.read().strip()
    result_tsclient.terminate()
    result_tsclient.wait()
    
    
arg = docopt.docopt(__doc__, version='0.2')

ip = arg["<ip>"]
logfile = arg["<logfile>"]
influx_node_ip = arg["<influx_node_ip>"]
influx_token = arg["<influx_token>"]
use_grafana = arg["<use_grafana>"]
path = arg["<path>"]
port = arg["<port>"]
