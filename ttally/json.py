"""
Programmatic interface to interact with this using JSON
"""

import json
from typing import NamedTuple, Dict, Any, Type, Iterator

from .common import namedtuple_func_name
from .file import glob_datafiles


# used in the export command, prints all info for a model without the
# overhead of parsing it into python objects first
def glob_json(nt: Type[NamedTuple]) -> Iterator[Dict[str, Any]]:
    for pth in glob_datafiles(namedtuple_func_name(nt)):
        yield from json.loads(pth.read_text())
