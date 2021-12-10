"""
Global functions which glob all data from the TTALLY_DATA_DIR
Used with 'hpi query' https://github.com/karlicoss/HPI
to access this from the command line

E.g. to grab how many things I've eaten within the last day
$ hpi query ttally.funcs.food --recent 1d | jq length
25
"""

from typing import Any

from .autotui_ext import glob_namedtuple
from .models import MODELS


# some metaprogramming hackery to create functions at the global level
# this intercepts any AttributeErrors thrown at a global level -- if the name
# you're trying to access/import matches a model name, it creates a function
# which returns the data for that


def __getattr__(name: str) -> Any:
    if name in MODELS:
        return lambda: glob_namedtuple(MODELS[name])
    raise AttributeError(f"No such attribute {name}")
