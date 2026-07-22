#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Created on Wed Jan 28 16:04:43 2026

#@author: jschlieffen


"""
Usage: tf_central_manager.py <logfile> <logfile_collectl>

Arguments: 
    <logfile> The Logfile to use
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
# This file starts mstool and flesnet on an entry node. It is started with 
#   srun nodelist=node input.py -N 1 <params>  
# After flesnet is started the program waits for a signal from the 
# central manager. If it receives a signal it will shut down flesnet and the 
# mstool. 
# NOTE: If the program does not terminate correctly, it completly suffices 
#       to just kill the srun process. One does not have to kill mstool and 
#       flesnet manually
# =============================================================================


def calc_str(ip,port):
    return f"-l 1 -c {ip}:{port}"

def write_response(node_name, msg):
    with open("tmp/nodes_response.txt", "w") as f:
        f.write(f"TF Central Manager {node_name}: done {msg}")
        f.flush()
        os.fsync(f.fileno())
    
def central_manager(ip,port,logfile,logfile_collectl,use_collectl,use_infiniband,path,influx_node_ip, influx_token, use_grafana):
    ip_string = calc_str(ip, port)
    node_name = subprocess.check_output(["hostname", "-s"]).decode().strip()
    channel = thread_channel.Channel()
    communicator = nc.communicator(channel, "TF_Central_Manager", node_name)
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
        #os.environ['CBM_INFLUX_TOKEN'] = influx_token
        grafana_string = '-m influx2:%s:timeslice_forwarder_state:%s' % (influx_node_ip, influx_token)
    cm_commands = (
        '%s./timeslice_forwarder %s %s > %s 2>&1 &' 
        % (path, ip_string, grafana_string ,logfile)
    )
    print(cm_commands)
    result_cm = subprocess.Popen(cm_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, preexec_fn=os.setsid)
    msg = ""
    while True:
        msg = channel.recv_from_child()
        match msg:
            case "kill":
                os.killpg(os.getpgid(result_cm.pid), signal.SIGKILL)
                channel.send_to_child("succeed")
            case "revieve":
                result_input_node = subprocess.Popen(cm_commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,preexec_fn=os.setsid)
                channel.send_to_child("succeed")
            case "stop":
                break
    if use_collectl == 1:
        #result_collectl.terminate()
        #result_collectl.wait()
        #result_collectl_cpu.terminate()
        #result_collectl_cpu.wait()
        collectl_communicater.put("exit")
        thread_collectl.join()
    result_cm.terminate()
    result_cm.wait()
    channel.send_to_child("succeed")
    communicator.join()
    
    

params = {}
with open('tmp/tf_cm_nodes_params.txt', 'r') as f:
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

ip = params.get('cm node ips')
arg = docopt.docopt(__doc__, version='0.2')
logfile = arg["<logfile>"]
logfile_collectl = arg['<logfile_collectl>']
#customize_string = "--timeslice-size 100 --processor-instances 0 -e \"../../../build/./tsclient -i shm:%s -o tcp://*:5556\""

central_manager(ip,port,logfile,logfile_collectl,use_collectl,use_infiniband,path, influx_node_ip, influx_token, use_grafana)

