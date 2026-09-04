#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 14 15:32:22 2026

@author: jschlieffen
"""

from interface import interactive_config_parser as cp
import curses
import interface.button as bu

class interface_params(cp.params_interactive):
    
    def __init__(self):
        super().__init__()

        self.active_field = None
        self.cursor_pos = 0
        self.scroll_pos = 0

        self.scroll_offset = 0
        self.max_scroll = 0
        
        
    def display_parameter(self,stdscr,label,value, x,y,field_width,selected=False,cursor_pos=0,scroll_pos=0):
        h, w = stdscr.getmaxyx()
        field_x = x + len(label) + 1
        if y < 0 or y >= h:
            return {
                "x": field_x,
                "y": y,
                "width": field_width,
                "height": 1,
                "value": str(value),
                "visible": False,
            }
        value_str = str(value)
        actual_width = min(field_width,max(1, w - field_x - 1))
        if cursor_pos < scroll_pos:
            scroll_pos = cursor_pos
        if cursor_pos >= scroll_pos + actual_width:
            scroll_pos = cursor_pos - actual_width + 1
        visible_value = value_str[scroll_pos: scroll_pos + actual_width]
        if x < w:
            visible_label = label[:w - x - 1]
            if visible_label:
                stdscr.addstr(y,x,visible_label)
        color = (curses.color_pair(6) if selected else curses.color_pair(5))
        stdscr.addstr(y,field_x, " " * actual_width,color)
        if visible_value:
            stdscr.addstr(y,field_x,visible_value,color)
        if selected:
            cursor_x = (field_x + cursor_pos - scroll_pos)
            if (field_x <= cursor_x < field_x + actual_width):
                stdscr.move(y,cursor_x)
        return {
            "x": field_x,
            "y": y,
            "width": actual_width,
            "height": 1,
            "value": value_str,
            "visible": True,
        }
                
        
    def display_input_file_list(self, stdscr, list_name, input_list, x, y):
        field_width_val = 20
        field_width_data = 10
        longest_name = max((len(name) for name, path, data in input_list),default=0)
        path_label_x = x + 2
        path_field_x = (path_label_x + longest_name + 1)
        data_label_x = (path_field_x + field_width_val + 4)
        data_field_x = (data_label_x + longest_name + 7)
        frame_x1 = x
        frame_y1 = y
        frame_x2 = (data_field_x + field_width_data + 2)
        frame_y2 = (y
            + 2
            + len(input_list) * 2
        )
        bu.draw_frame(
            stdscr,
            frame_y1,
            frame_x1,
            frame_y2,
            frame_x2
        )
        stdscr.addstr(
            y,
            x + 2,
            list_name,
            curses.color_pair(4) | curses.A_BOLD
        )
        fields = []
        y += 2
        for index, (name, path, data) in enumerate(input_list):
            path_field = self.display_parameter(
                stdscr,
                f"{name}:",
                path,
                path_label_x,
                y,
                field_width_val,
                selected=(
                    self.active_field is not None
                    and self.active_field["index"] == index
                    and self.active_field["type"] == "path"
                ),
                cursor_pos=(
                    self.cursor_pos
                    if (
                        self.active_field is not None
                        and self.active_field["index"] == index
                        and self.active_field["type"] == "path"
                    )
                    else 0
                ),
                scroll_pos=(
                    self.scroll_pos
                    if (
                        self.active_field is not None
                        and self.active_field["index"] == index
                        and self.active_field["type"] == "path"
                    )
                    else 0
                )
            )
            data_field = self.display_parameter(
                stdscr,
                f"{name}_data:",
                data,
                data_label_x,
                y,
                field_width_data,
                selected=(
                    self.active_field is not None
                    and self.active_field["index"] == index
                    and self.active_field["type"] == "data"
                ),
                cursor_pos=(
                    self.cursor_pos
                    if (
                        self.active_field is not None
                        and self.active_field["index"] == index
                        and self.active_field["type"] == "data"
                    )
                    else 0
                ),
                scroll_pos=(
                    self.scroll_pos
                    if (
                        self.active_field is not None
                        and self.active_field["index"] == index
                        and self.active_field["type"] == "data"
                    )
                    else 0
                )
            )
            fields.append({
                "index": index,
                "type": "path",
                "name": name,
                "value": str(path),
                **path_field,
            })
            fields.append({
                "index": index,
                "type": "data",
                "name": name,
                "value": str(data),
                **data_field,
            })
            y += 2
        return fields
    
    
    def display_node_list(self,
        stdscr,
        list_name,
        input_list,
        x,
        y
    ):
        field_width = 30
    
        frame_x1 = x
        frame_y1 = y
    
        longest_name = max(
            (len(name) for name, path, data in input_list),
            default=0
        )
    
        field_x = x + longest_name + 5
    
        frame_x2 = field_x + field_width + 2
        frame_y2 = y + len(input_list) * 2 + 2
    
        bu.draw_frame(
            stdscr,
            frame_y1,
            frame_x1,
            frame_y2,
            frame_x2
        )
    
        stdscr.addstr(
            y,
            x + 2,
            list_name,
            curses.color_pair(4) | curses.A_BOLD
        )
    
        fields = []
    
        y += 2
    
        for index, (name, path, data) in enumerate(input_list):
    
            label = f"{name}:"
    
            field = self.display_parameter(
                stdscr,
                label,
                path,
                x + 2,
                y,
                field_width,
                selected=(
                    self.active_field is not None
                    and self.active_field["index"] == index
                    and self.active_field["type"] == "node"
                ),
                cursor_pos=(
                    self.cursor_pos
                    if (
                        self.active_field is not None
                        and self.active_field["index"] == index
                        and self.active_field["type"] == "node"
                    )
                    else 0
                ),
                scroll_pos=(
                    self.scroll_pos
                    if (
                        self.active_field is not None
                        and self.active_field["index"] == index
                        and self.active_field["type"] == "node"
                    )
                    else 0
                )
            )
    
            fields.append({
                "index": index,
                "type": "node",
                "name": name,
                "value": str(path),
                "original_type": type(path),
                **field,
            })
    
            y += 2
    
        return fields
                    
    def display_parameter_groups(self, win, x, y, width, height, scroll_offset):
        fields = []
        content_y = y
        ignored_groups = {'node list','input files',}
        for group_name, parameters in self.groups.items():
            if group_name in ignored_groups:
                continue
            visible_parameters = [p for p in parameters if p in self.display_params]
            if not visible_parameters:
                continue
            longest_label = max(len(str(p)) for p in visible_parameters)
            field_width = max(15, width - longest_label - 8)
            group_height = len(visible_parameters) + 2
            frame_y1 = content_y - scroll_offset
            frame_y2 = (frame_y1 + group_height - 1)
            frame_x1 = x
            frame_x2 = x + width - 1
            if (frame_y2 >= 0 and frame_y1 < height):
                if (frame_y1 >= 0 and frame_y2 < height):
                    bu.draw_frame(win, frame_y1,frame_x1,frame_y2,frame_x2)
            param_y = (content_y + 1 - scroll_offset)
            for param in visible_parameters:
                value = getattr(self.Par_,param)
                if (self.active_field is not None and self.active_field["param"] == param):
                    value = self.active_field["value"]
                selected = (self.active_field is not None and self.active_field["param"] == param)
                if 0 <= param_y < height:
                    field = self.display_parameter(win, f"{param}:", value, x + 2, param_y,field_width,selected=selected,
                                                    cursor_pos=(self.cursor_pos if selected else 0),
                                                    scroll_pos=(self.scroll_pos if selected else 0)
                                                   )
                else:
                    field = {
                        "x": (x + 2+ len(f"{param}:")+ 1),
                        "y": param_y,
                        "width": field_width,
                        "height": 1,
                        "value": str(value),
                        "visible": False,
                    }
                fields.append({
                    "param": param,
                    "value": str(value),
                    "original_type": type(getattr(self.Par_, param)),
                    "section": self.get_param_section(param),
                    **field
                })
    
                param_y += 1
            content_y += group_height + 1
        return fields, content_y





    def handle_parameter_mouse(self,mx,my,fields):
        for field in fields:
            if not field.get("visible", True):
                continue
            if (field["x"] <= mx < field["x"] + field["width"] and field["y"] <= my < field["y"] + field["height"]):
                self.active_field = field.copy()
                relative_x = mx - field["x"]
                self.cursor_pos = min(len(field["value"]), relative_x)
                self.scroll_pos = max(0, self.cursor_pos - field["width"]+ 1)
                return True
        return False
    
        
    def handle_parameter_key(self, key):
        if self.active_field is None:
            return
        field = self.active_field
        value = field["value"]
        if key == curses.KEY_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
        elif key == curses.KEY_RIGHT:
            self.cursor_pos = min(len(value),self.cursor_pos + 1)
        elif key == curses.KEY_HOME:
            self.cursor_pos = 0
        elif key == curses.KEY_END:
            self.cursor_pos = len(value)
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if self.cursor_pos > 0:
                value = (value[:self.cursor_pos - 1] + value[self.cursor_pos:])
                self.cursor_pos -= 1
        elif key == curses.KEY_DC:
            if self.cursor_pos < len(value):
                value = (value[:self.cursor_pos] + value[self.cursor_pos + 1:])
        elif key in (curses.KEY_ENTER, 10,13):
            self.commit_parameter()
            return
        elif key == 27:
            self.active_field = None
            self.cursor_pos = 0
            self.scroll_pos = 0
            return
        elif 32 <= key <= 126:
            value = (value[:self.cursor_pos] + chr(key) + value[self.cursor_pos:])
            self.cursor_pos += 1
        else:
            return
        self.active_field["value"] = value
        self.scroll_pos = max(0,self.cursor_pos - self.active_field["width"] + 1)
        
        
        
    def commit_parameter(self):
        if self.active_field is None:
            return
        field = self.active_field
        param = field["param"]
        section = field["section"]
        value = field["value"]
        original_type = field["original_type"]
        try:
            if original_type is bool:
                value_lower = value.lower()
                if value_lower in ("true","1","yes", "on"):
                    value = True
                elif value_lower in ("false","0", "no","off"):
                    value = False
                else:
                    return
            elif original_type is int:
                value = int(value)
            elif original_type is float:
                value = float(value)
        except ValueError:
            return
        self.change_param(section, param, value)
        self.active_field = None
        self.cursor_pos = 0
        self.scroll_pos = 0
    
    
    def commit_field(self, input_list):
        if self.active_field is None:
            return
        self.active_field = None
        self.cursor_pos = 0
        self.scroll_pos = 0