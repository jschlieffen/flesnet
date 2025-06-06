#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed May 14 17:14:05 2025

#@author: jschlieffen

"""
Usage: timeslice_forwarding.py <logfile> <build_node_ip> <influx_node_ip> <influx_token> <use_grafana> <path> <port> <write_data_to_file> <analyze_data> <use_infiniband> <use_collectl> <logfile_collectl>

Arguments:
    
    <logfile> The Logfile to use
    <build_node_ip> The ip address to use
    <influx_node_ip> The ip of the where the influx container is runnning
    <influx_token> The token to the influx-db
    <use_grafana> enables/disables grafana
    <path> The path to tsclient
    <port> The port for the timeslice-forwarding
    <write_data_to_file> The file, where the timeslices should be saved. To deactivate the saving use -1
    <analyze_data> activates the -a flag in the tsclient
    <use_infiniband> Decides whether infiniband shall be used or ethernet
    <use_collectl> Decides if collectl should be used for tracking the network usage
    <logfile_collectl> The csv-file which collectl should use
"""

import subprocess
import time
import docopt
import sys
import os


#may be extended
def calc_ip_str(ip,port,write_data_to_file,path,analyze_data):
    ip_string = f"tcp://{ip}:{port}"
    if write_data_to_file == '0':
        output_file_string = ""
    else:
        output_file_string = f"-o file://{path}{write_data_to_file}"
    if analyze_data == '1':
        analyze_data_string = "-a"
    else:
        analyze_data_string = ""
    return ip_string,output_file_string,analyze_data_string

def start_collectl(use_infiniband, csvfile_name):
    if use_infiniband == '1':
        collectl_command = f"sudo collectl --plot --sep , -i 1 -sx > {csvfile_name}"
        print(collectl_command)
    else:
        collectl_command = f"collectl --plot --sep , -i 1 -sn > {csvfile_name}"
    result_collectl = subprocess.Popen(collectl_command,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(1)
    return result_collectl

def start_collectl_cpu(csv_file_name):
    cpu_csv_file_name = csv_file_name.replace(".csv", "_cpu_usage.csv")
    collectl_command = f"collectl --plot --sep , -i 1 -sC > {cpu_csv_file_name}"
    result_collectl = subprocess.Popen(collectl_command,shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(1)
    return result_collectl

def main(ip,logfile,influx_node_ip, influx_token, use_grafana,path, port,write_data_to_file, analyze_data, use_infiniband, use_collectl, logfile_collectl):
    ip_string,output_file_string,analyze_data_string = calc_ip_str(ip, port, write_data_to_file, path, analyze_data)
    if use_collectl == '1':
        result_collectl = start_collectl(use_infiniband, logfile_collectl)
        result_collectl_cpu = start_collectl_cpu(logfile_collectl)
    grafana_string = ''
    if use_grafana == '1':
        os.environ['CBM_INFLUX_TOKEN'] = influx_token
        grafana_string = '-m influx2:%s:8086:tsclient_status: ' % (influx_node_ip)
    tsclient_commands = (
            '%s./tsclient -l 1 -L %s -i %s %s %s %s > /dev/null 2>&1 &'
            % (path,logfile,ip_string, analyze_data_string, output_file_string, grafana_string)
        )
    
    result_tsclient = subprocess.Popen(tsclient_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    input_data = ''
    while input_data == '':
        input_data = sys.stdin.read().strip()
    if use_collectl == '1':
        result_collectl.terminate()
        result_collectl.wait()
        result_collectl_cpu.terminate()
        result_collectl_cpu.wait()
    result_tsclient.terminate()
    result_tsclient.wait()
    
    
arg = docopt.docopt(__doc__, version='0.2')

ip = arg["<build_node_ip>"]
logfile = arg["<logfile>"]
influx_node_ip = arg["<influx_node_ip>"]
influx_token = arg["<influx_token>"]
use_grafana = arg["<use_grafana>"]
path = arg["<path>"]
port = arg["<port>"]
write_data_to_file = arg['<write_data_to_file>']
analyze_data = arg['<analyze_data>']
use_infiniband = arg['<use_infiniband>']
use_collectl = arg['<use_collectl>']
logfile_collectl = arg['<logfile_collectl>']

main(ip,logfile,influx_node_ip, influx_token, use_grafana,path, port,write_data_to_file, analyze_data, use_infiniband, use_collectl, logfile_collectl)