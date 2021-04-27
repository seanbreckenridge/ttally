import inspect
from pathlib import Path
from datetime import datetime
from typing import NamedTuple, Any, Iterator, Optional, Type
from itertools import chain

from autotui.shortcuts import load_prompt_and_writeback, load_from
from autotui.typehelpers import strip_optional

from .file import datafile, glob_datafiles


# TODO: move this away from autotui_ext?
def namedtuple_func_name(nt: Type[NamedTuple]) -> str:
    assert hasattr(nt, "_fields"), "Did not receive a valid NamedTuple!"
    return str(nt.__name__.casefold())


# load, prompt and writeback one of the models
def prompt(nt: Type[NamedTuple]) -> None:
    f: Path = datafile(namedtuple_func_name(nt))
    load_prompt_and_writeback(nt, f)


def namedtuple_extract_from_annotation(nt: Type[NamedTuple], _type: Any) -> str:
    """
    >>> from typing import NamedTuple; from datetime import datetime
    >>> class Test(NamedTuple): something: datetime
    >>> namedtuple_extract_from_annotation(Test, datetime)
    'something'
    """
    for attr_name, param in inspect.signature(nt).parameters.items():
        param_type, _ = strip_optional(param.annotation)
        if param_type == _type:
            return attr_name
    raise TypeError(f"Could not find {_type} on {nt}")


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
