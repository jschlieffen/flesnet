#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 24 21:16:17 2026

@author: jschlieffen
"""

import execution as ex
#import interface.main_frame as main_frame
import interface.flesctrl_starter as starter
import interface.new_main_frame as main_frame
import curses
import subprocess
import shutil
import sys
import argparse

def get_params():
    file_names = []
    with open('tmp/interface/interface_params.txt', 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith("file_name:"):
                _, data = line.split("file_name: ")
                logfile, file_data = data.split(", ")
                print(logfile)
                file_names.append(logfile)
            elif line.startswith("num_receivers: "):
                num_receivers = int(line.split(": ")[1])
            elif line.startswith("num_inputnodes: "):
                num_inputnodes = int(line.split(": ")[1])
            elif line.startswith("num_outputnodes: "):
                num_outputnodes = int(line.split(": ")[1])
            elif line.startswith("num_cm: "):
                num_cm = int(line.split(": ")[1])
            elif line.startswith("enable_graph:"):
                enable_graph = line.split(": ")[1] == '1'
            elif line.startswith("enable_progess_bar:"):
                enable_progess_bar = line.split(": ")[1] == '1'
            elif line.startswith("use_GSI_TS_forwarding: "):
                use_GSI_TS_forwarding = line.split(": ")[1] == '1'
            elif line.startswith("use_ZIB_TS_forwarding: "):
                use_ZIB_TS_forwarding = line.split(": ")[1] == '1'
    parameters = {
        "num_receiver_nodes": num_receivers,
        "num_input_nodes": num_inputnodes,
        "num_output_nodes": num_outputnodes,
        "num_cm": num_cm,
        "use_GSI_TS_forwarding": use_GSI_TS_forwarding,
        "use_ZIB_TS_forwarding": use_ZIB_TS_forwarding,
    }
    return file_names, parameters

def create_com_files():
    with open('tmp/interface/interface_response.txt','w') as f:
        f.write('tm')
        f.close()
    with open('tmp/interface/interface_commands.txt','w') as f:
        f.write('tm')
        f.close()

def main_V2():
    create_com_files()
    shutil.copy2("setup/config.cfg", "setup/config_interactive.cfg")
    result = curses.wrapper(main_frame.main_start_frame)
    if result == 'exit':
        sys.exit(1)
    elif result == 'start':
        starter.start_flesctrl()
    elif result == 'alloc':
        starter.allocate_nodes()
    result = curses.wrapper(main_frame.main_intermediate_frame)
    if result == 'exit':
        starter.stop_flesctrl()
    file_names,parameters = get_params()
    result = curses.wrapper(main_frame.main_frame, file_names,parameters)
    if result == 'stop':
        starter.stop_flesctrl()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--attach_session",
        action="store_true",
        help="Run in interactive mode"
    )
    
    args = parser.parse_args()
    
    attach_session = args.attach_session
    if not attach_session:
        create_com_files()
        shutil.copy2("setup/config.cfg", "setup/config_interactive.cfg")
    flesapp = main_frame.flesApp(attach_session)
    flesapp.run()


    
if __name__ == "__main__":
    main()