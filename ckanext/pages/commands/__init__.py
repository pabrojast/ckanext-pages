# -*- coding: utf-8 -*-
from .fix_datasets import get_commands as fix_datasets_commands
from .import_ai_tools import get_commands as import_ai_tools_commands
from .seed_crida import get_commands as seed_crida_commands
from .data_stories import get_commands as data_stories_commands


def get_commands():
    """Return all available commands"""
    commands = []
    commands.extend(fix_datasets_commands())
    commands.extend(import_ai_tools_commands())
    commands.extend(seed_crida_commands())
    commands.extend(data_stories_commands())
    return commands