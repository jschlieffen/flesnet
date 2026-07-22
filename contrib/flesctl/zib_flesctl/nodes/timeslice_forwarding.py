#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed May 14 17:14:05 2025

#@author: jschlieffen

"""
Usage: timeslice_forwarding.py <logfile> <build_node_ip> <logfile_collectl>

Arguments:
    
    <logfile> The Logfile to use
    <build_node_ip> The ip address to use
    <logfile_collectl> The csv-file which collectl should use
"""

import subprocess
import time
import docopt
import sys
import os
import threading 
import queue
import signal
import nodes_communicator as nc
import thread_channel
import nodes_help_functions as nh
# =============================================================================
# This file starts the tsclient on a given node to a given build node 
#   srun nodelist=node timeslice_forwarding.py -N 1 <params>  
# After the tsclient is started the program waits for a signal from the 
# central manager. If it receives a signal it will shut down the tsclient
# NOTE: If the program does not terminate correctly, it completly suffices 
#       to just kill the srun process. One does not have to kill mstool and 
#       flesnet manually
# =============================================================================
#may be extended
def calc_ip_str(ip,port,write_data_to_file,path,analyze_data,node_name,path_to_output_file):
    ip_string = f"tcp://{ip}:{port}"
    if write_data_to_file == 0:
        output_file_string = ""
    else:
        with open('tmp/Run_folder_name.txt','r') as file:
            run_id = file.read().strip()
            file.close()
        output_file_string = f"-o file:{path_to_output_file}/{run_id}/tsa_files/output_node_{node_name}.tsa"
    if analyze_data == 1:
        analyze_data_string = "-a"
    else:
        analyze_data_string = ""
    return ip_string,output_file_string,analyze_data_string


def main(ip,logfile,influx_node_ip, influx_token, use_grafana,path, port,write_data_to_file, analyze_data, use_infiniband, use_collectl, logfile_collectl, path_to_output_file):
    node_name = subprocess.check_output(["hostname", "-s"]).decode().strip()
    ip_string,output_file_string,analyze_data_string = calc_ip_str(ip, port, write_data_to_file, path, analyze_data,node_name,path_to_output_file)
    channel = thread_channel.Channel()
    communicator = nc.communicator(channel, "Receiver", node_name)
    communicator.start()
    if use_collectl == 1:
        basename = os.path.splitext(os.path.basename(logfile_collectl))[0]
        filename_cpus = f"tmp/{basename}.txt"
        nh.get_alloc_cpus(filename_cpus)
        #+result_collectl = start_collectl(use_infiniband, logfile_collectl)
        #result_collectl_cpu = start_collectl_cpu(logfile_collectl)
        collectl_communicater = queue.Queue()
        thread_collectl = threading.Thread(target=nh.start_collectl_thread, args=(use_infiniband, logfile_collectl, collectl_communicater))
        thread_collectl.start()
        time.sleep(1)
    grafana_string = ''
    if use_grafana == 1:
        os.environ['CBM_INFLUX_TOKEN'] = influx_token
        grafana_string = '--monitor influx2:%s:8086:tsclient_status: ' % (influx_node_ip)
    tsclient_commands = (
            '%s./tsclient -l 1 -L %s -i %s %s %s %s > /dev/null 2>&1 &'
            % (path,logfile,ip_string, analyze_data_string, output_file_string, grafana_string)
        )
    print(tsclient_commands)
    result_tsclient = subprocess.Popen(tsclient_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
    msg = ""
    while True:
        msg = channel.recv_from_child()
        match msg:
            case "kill":
                os.killpg(os.getpgid(result_tsclient.pid), signal.SIGKILL)
                channel.send_to_child("succeed")
            case "revieve":
                result_tsclient = subprocess.Popen(tsclient_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
                channel.send_to_child("succeed")
            case "stop":

                break
    if use_collectl == 1:
        collectl_communicater.put("exit")
        thread_collectl.join()
    result_tsclient.terminate()
    result_tsclient.wait()
    channel.send_to_child("succeed")
    communicator.join()
    

params = {}
with open('tmp/receiving_nodes_params.txt', 'r') as f:
    print('test1')
    for line in f:
        if ':' in line:
            key, value = line.strip().split(':', 1)
            value = value.strip()
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            else:
                try:
                    value = int(value)
                except ValueError:
                    pass
            params[key] = value

for key, value in params.items():
    globals()[key] = value
    
arg = docopt.docopt(__doc__, version='0.2')

ip = arg["<build_node_ip>"]
logfile = arg["<logfile>"]
logfile_collectl = arg['<logfile_collectl>']

main(ip,logfile,influx_node_ip, influx_token, use_grafana,path, port,write_data_to_file, analyze_data, use_infiniband, use_collectl, logfile_collectl,path_to_output_file)