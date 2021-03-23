"""
Programmatic interface to save a blob without user interaction
"""

import sys
from typing import List, NamedTuple, Any

from autotui import namedtuple_sequence_loads
from autotui.shortcuts import dump_to

from .autotui_ext import load_from_safe, namedtuple_func_name
from .file import datafile


# used in __main__.py for the from_json command
def save_from_stdin(nt: Any) -> None:
    json_blob: str = sys.stdin.read()
    p = datafile(namedtuple_func_name(nt))
    items: List[NamedTuple] = load_from_safe(nt, p)
    new_items: List[NamedTuple] = namedtuple_sequence_loads(json_blob, nt)
    items.extend(new_items)
    dump_to(items, p)
