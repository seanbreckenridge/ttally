import warnings
import inspect
from pathlib import Path
from datetime import datetime
from typing import NamedTuple, Any, Dict, Callable, List, Iterator, Optional
from itertools import chain

from autotui.shortcuts import load_prompt_and_writeback, load_from
from autotui.namedtuple_prompt import namedtuple_prompt_funcs
from autotui.typehelpers import strip_optional

from .file import datafile, glob_datafiles


def load_from_safe(to: NamedTuple, path: Path) -> List[NamedTuple]:
    if not path.exists():
        warnings.warn(f"{path} did not exist, returning empty list")
        return []
    else:
        return load_from(to, path)


# TODO: move this away from autotui_ext?
def namedtuple_func_name(nt: Any) -> str:
    assert hasattr(nt, "_fields"), "Did not receive a valid NamedTuple!"
    return str(nt.__name__.casefold())


# load, prompt and writeback one of the models
def prompt(nt: Any) -> None:
    f: Path = datafile(namedtuple_func_name(nt))
    load_prompt_and_writeback(nt, f)


def namedtuple_extract_from_annotation(nt: Any, _type: Any) -> str:
    """
    class Test(NamedTuple):
        something: datetime

    >>> namedtuple_extract_from_annotation(Test, datetime)
    "something"
    """
    for attr_name, param in inspect.signature(nt).parameters.items():
        param_type, _ = strip_optional(param.annotation)
        if param_type == _type:
            return attr_name
    raise TypeError(f"Could not find {_type} on {nt}")


# prompts, but sets the datetime to now
def namedtuple_prompt_now(nt: Any) -> Any:
    # grab the functions generated by autotui and replace the 'datetime' handler
    # with datetime.now()
    funcs: Dict[str, Callable[[], Any]] = namedtuple_prompt_funcs(nt)
    datetime_attr_name = namedtuple_extract_from_annotation(nt, datetime)
    funcs[datetime_attr_name] = lambda: datetime.now()
    nt_values: Dict[str, Any] = {
        attr_key: attr_func() for attr_key, attr_func in funcs.items()
    }
    return nt(**nt_values)


# prompt, but set the datetime for the resulting nametuple to now
def prompt_now(nt: NamedTuple) -> None:
    # load items from file
    p: Path = datafile(namedtuple_func_name(nt))
    # the lambda is to match the argument count
    # of the prompt_namedtuple function from autotui
    nt_wrapped = lambda n, _a, _t: namedtuple_prompt_now(n)
    load_prompt_and_writeback(nt, p, prompt_function=nt_wrapped)


# takes one of the models.py and loads all data from it
def glob_namedtuple(nt: Any, in_dir: Optional[Path] = None) -> Iterator[Any]:
    yield from chain(
        *map(
            lambda p: load_from_safe(nt, p),
            glob_datafiles(namedtuple_func_name(nt), in_dir=in_dir),
        )
    )
