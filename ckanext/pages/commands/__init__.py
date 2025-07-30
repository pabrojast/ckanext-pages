# -*- coding: utf-8 -*-
from .fix_datasets import get_commands as fix_datasets_commands

def get_commands():
    """Return all available commands"""
    commands = []
    commands.extend(fix_datasets_commands())
    return commands