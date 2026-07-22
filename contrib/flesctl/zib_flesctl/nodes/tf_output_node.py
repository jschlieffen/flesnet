#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed Jan 28 19:02:26 2026

#@author: jschlieffen



"""
Usage: tf_output_node.py <logfile> <output_node_idx> <output_node_ip> <logfile_collectl> <logfile_tsclient>

Arguments: 
    <logfile> The Logfile to use
    <output_node_idx> The index of the current entry node
    <output_node_ip> The ip of the output node
    <logfile_collectl> The csv-file which collectl should use
    <logfile_tsclient> The logfile for the tsclient if used
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
# This file starts mstool and flesnet on an entry node. It is started with 
#   srun nodelist=node input.py -N 1 <params>  
# After flesnet is started the program waits for a signal from the 
# central manager. If it receives a signal it will shut down flesnet and the 
# mstool. 
# NOTE: If the program does not terminate correctly, it completly suffices 
#       to just kill the srun process. One does not have to kill mstool and 
#       flesnet manually
# =============================================================================

def calc_str(output_node_ip,port,cm_node_ip,output_node_idx, num_components, desc_size, data_size):
    shm_str = f"ts_in_{output_node_idx}"
    str_ = f"-l 1 -A {output_node_ip}:{port} -c {cm_node_ip}:{port} -N {output_node_idx} -o {shm_str}?n={num_components}\\&descsize={desc_size}\\&datasize={data_size}"
    return str_,shm_str


        
def start_tsclient(path,shm_str,node_name,write_data_to_file,analyze_data, logfile_tsclient, 
                   path_to_output_file, influx_node_ip, influx_token, use_grafana, tsclient_communicater):
    str_ = f"-L {logfile_tsclient} "
    if analyze_data:
        str_ += "-a "
    if write_data_to_file:
        with open('tmp/Run_folder_name.txt','r') as file:
            run_id = file.read().strip()
            file.close()
        str_ += f"-o file:{path_to_output_file}/{run_id}/tsa_files/output_node_{node_name}.tsa"
    if use_grafana:
        os.environ['CBM_INFLUX_TOKEN'] = influx_token
        str_ += f" --monitor influx2:{influx_node_ip}:tsclient_status:" 
    tsclient_command = f"{path}./tsclient -i shm:{shm_str} {str_}"
    print(tsclient_command)
    result_tsclient = subprocess.Popen(tsclient_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    #result_tsclient.wait()
    while True:
        msg = tsclient_communicater.get()
        if msg == 'exit':
            result_tsclient.terminate()
            result_tsclient.wait()
            break

def output_node(output_node_ip,port,cm_node_ip,output_node_idx,use_collectl,use_infiniband, path, write_data_to_file, analyze_data, num_components, desc_size, data_size,
                logfile_tsclient,path_to_output_file, influx_node_ip, influx_token, use_grafana):
    str_,shm_str = calc_str(output_node_ip,port,cm_node_ip,output_node_idx, num_components, desc_size, data_size)
    node_name = subprocess.check_output(["hostname", "-s"]).decode().strip()
    channel = thread_channel.Channel()
    communicator = nc.communicator(channel, "TF_Output", node_name)
    communicator.start()
    if use_collectl == 1:
        basename = os.path.splitext(os.path.basename(logfile))[0]
        filename_cpus = f"tmp/{basename}.txt"
        nh.get_alloc_cpus(filename_cpus)
        #result_collectl = start_collectl(use_infiniband, logfile_collectl)
        #result_collectl_cpu = start_collectl_cpu(logfile_collectl)
        collectl_communicater = queue.Queue()
        thread_collectl = threading.Thread(target=nh.start_collectl_thread, args=(use_infiniband, logfile_collectl, collectl_communicater))
        thread_collectl.start()
        time.sleep(1)

    grafana_string = ''
    if use_grafana == 1:
        grafana_string = '-m influx2:%s:timeslice_forwarder_state:%s' % (influx_node_ip, influx_token) 
    tsclient_communicater = queue.Queue()
    thread_tsclient = threading.Thread(target=start_tsclient, args=(path, shm_str, node_name, write_data_to_file, analyze_data, logfile_tsclient,
                                                                    path_to_output_file, influx_node_ip, influx_token, use_grafana, tsclient_communicater))
    thread_tsclient.start()
    output_node_commands = (
        '%s./timeslice_forwarder %s %s > %s 2>&1 &' 
        % (path,str_, grafana_string,logfile)
    )
    print(output_node_commands)
    result_output_node = subprocess.Popen(output_node_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
    msg = ""
    while True:
        msg = channel.recv_from_child()
        match msg:
            case "kill":
                os.killpg(os.getpgid(result_output_node.pid), signal.SIGKILL)
                channel.send_to_child("succeed")
            case "revieve":
                result_output_node = subprocess.Popen(output_node_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
                channel.send_to_child("succeed")
            case "stop":
                break
    if use_collectl == 1:
        collectl_communicater.put("exit")
        thread_collectl.join()
    tsclient_communicater.put("exit")
    thread_tsclient.join()
    result_output_node.terminate()
    result_output_node.wait()
    channel.send_to_child("succeed")
    communicator.join()
    
    

params = {}

with open('tmp/tf_output_nodes_params.txt', 'r') as f:
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
    f.close()


for key, value in params.items():
    globals()[key] = value
cm_node_ip = params.get('cm node ips')

arg = docopt.docopt(__doc__, version='0.2')
logfile = arg["<logfile>"]
output_node_idx = arg["<output_node_idx>"]
output_node_ip = arg["<output_node_ip>"]
logfile_collectl = arg['<logfile_collectl>']
logfile_tsclient = arg['<logfile_tsclient>']
#customize_string = "--timeslice-size 100 --processor-instances 0 -e \"../../../build/./tsclient -i shm:%s -o tcp://*:5556\""

output_node(output_node_ip,port,cm_node_ip,output_node_idx,use_collectl,use_infiniband, path, write_data_to_file, analyze_data, num_components, desc_size, data_size,
            logfile_tsclient,path_to_output_file,influx_node_ip, influx_token, use_grafana)
