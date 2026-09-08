#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Aug 27 16:00:50 2026

@author: jschlieffen
"""
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Input, Static, Checkbox


class ParameterEditor(VerticalScroll):

    def __init__(self, parameters, **kwargs):
        super().__init__(**kwargs)
        self.parameters = parameters

    def compose(self):
        for group_name, group_parameters in self.parameters.groups.items():
            visible_parameters = [param for param in group_parameters if param in self.parameters.display_params]
            if not visible_parameters:
                continue
            yield Static(
                group_name,
                classes="group-title",
            )
            for param in visible_parameters:
                value = self.parameters.get_param_value(param)
                yield Horizontal(
                    Static(
                        f"{param}:",
                        classes="parameter-label",
                    ),
                    self.make_editor(param, value),
                    classes="parameter-row",
                )

    def make_editor(self, param, value):
        if isinstance(value, bool):
            return Checkbox(
                value=value,
                id=f"param-{param}",
            )
        return Input(value=str(value), id=f"param-{param}")

    async def on_input_submitted(self, event: Input.Submitted):
        param = event.input.id.removeprefix("param-")
        value = event.input.value
        if self.commit_parameter(param, value):
            self.app.notify(f"{param} updated")
            await self.recompose()
        else:
            self.app.notify(f"Invalid value for {param}", severity="error")

    async def on_checkbox_changed(self, event: Checkbox.Changed):
        param = event.checkbox.id.removeprefix("param-")
        if self.commit_parameter(param,event.value):
            self.app.notify(f"{param} updated")
            await self.recompose()
        else:
            self.app.notify(f"Could not update {param}", severity="error")

    def commit_parameter(self, param, value):
        try:
            current_value = (self.parameters.get_param_value(param))
        except AttributeError:
            return False
        original_type = type(current_value)
        try:
            if original_type is bool:
                if isinstance(value, bool):
                    new_value = value
                else:
                    value = str(value).lower()
                    if value in ("true","1", "yes", "on"):
                        new_value = True
                    elif value in ("false","0", "no","off"):
                        new_value = False
                    else:
                        return False
            elif original_type is int:
                new_value = int(value)
            elif original_type is float:
                new_value = float(value)
            else:
                new_value = str(value)
        except (ValueError, TypeError):
            return False
        section = self.parameters.get_param_section(param)
        if section is None:
            return False
        self.parameters.change_param(section,param,new_value)
        return True
