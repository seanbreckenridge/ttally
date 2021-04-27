import sys
from pathlib import Path
from datetime import datetime
from typing import NamedTuple, Iterator, Optional, Type, List
from itertools import chain

from autotui import namedtuple_sequence_loads
from autotui.shortcuts import load_prompt_and_writeback, load_from, dump_to

from .file import datafile, glob_datafiles
from .common import namedtuple_func_name


# load, prompt and writeback one of the models
def prompt(nt: Type[NamedTuple]) -> None:
    f: Path = datafile(namedtuple_func_name(nt))
    load_prompt_and_writeback(nt, f)


# prompt, but set the datetime for the resulting nametuple to now
def prompt_now(nt: Type[NamedTuple]) -> None:
    # load items from file
    p: Path = datafile(namedtuple_func_name(nt))
    load_prompt_and_writeback(nt, p, type_use_values={datetime: datetime.now})


# takes one of the models.py and loads all data from it
def glob_namedtuple(
    nt: Type[NamedTuple], in_dir: Optional[Path] = None
) -> Iterator[NamedTuple]:
    yield from chain(
        *map(
            lambda p: load_from(nt, p, allow_empty=True),
            glob_datafiles(namedtuple_func_name(nt), in_dir=in_dir),
        )
    )


# used in __main__.py for the from_json command
def save_from_stdin(nt: Type[NamedTuple]) -> None:
    json_blob: str = sys.stdin.read()
    p = datafile(namedtuple_func_name(nt))
    items: List[NamedTuple] = load_from(nt, p, allow_empty=True)
    new_items: List[NamedTuple] = namedtuple_sequence_loads(json_blob, nt)
    items.extend(new_items)
    dump_to(items, p)
