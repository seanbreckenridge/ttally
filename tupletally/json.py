"""
Programmatic interface to interact with this using JSON
"""

import sys
import json
from typing import NamedTuple, Dict, Any, List, Type

from autotui import namedtuple_sequence_loads
from autotui.shortcuts import dump_to

from .autotui_ext import load_from_safe, namedtuple_func_name
from .file import datafile, glob_datafiles


# used in __main__.py for the from_json command
def save_from_stdin(nt: Type[NamedTuple]) -> None:
    json_blob: str = sys.stdin.read()
    p = datafile(namedtuple_func_name(nt))
    items: List[NamedTuple] = load_from_safe(nt, p)
    new_items: List[NamedTuple] = namedtuple_sequence_loads(json_blob, nt)
    items.extend(new_items)
    dump_to(items, p)


# used in the export command, prints all info for a model without the
# overhead of parsing it into python objects first
def glob_json(nt: Type[NamedTuple]) -> List[Dict[str, Any]]:
    res: List[Dict[str, Any]] = []
    for p in glob_datafiles(namedtuple_func_name(nt)):
        res.extend(json.loads(p.read_text()))
    return res
