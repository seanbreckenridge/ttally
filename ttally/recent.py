from typing import Iterator, List, NamedTuple, Type, Callable
from datetime import datetime

import more_itertools

from .autotui_ext import glob_namedtuple
from .common import namedtuple_extract_from_annotation


def _extract_dt_from(nt: Type[NamedTuple]) -> Callable[[NamedTuple], datetime]:
    # returns a function, when which given an item of this
    # type, returns the datetime value
    dt_attr: str = namedtuple_extract_from_annotation(nt, datetime)
    return lambda o: getattr(o, dt_attr)  # type: ignore[no-any-return]


def query_recent(nt: Type[NamedTuple], count: int) -> List[NamedTuple]:
    """query the module for recent entries (based on datetime) from a namedtuple"""
    items: List[NamedTuple] = more_itertools.take(
        count,
        sorted(glob_namedtuple(nt), key=_extract_dt_from(nt), reverse=True),
    )
    return items


def query_print(nt: Type[NamedTuple], count: int) -> None:
    # assumes that there is a datetime attribute on this, else
    # we have nothing to sort by
    res: Iterator[NamedTuple] = iter(query_recent(nt, count))
    res = more_itertools.peekable(res)
    try:
        first_item = res.peek()  # namedtuple-like
    except StopIteration:
        raise RuntimeError(f"data queried from {nt} was empty")
    dt_attr: str = namedtuple_extract_from_annotation(first_item.__class__, datetime)
    # get non-datetime attr names
    other_attrs: List[str] = [k for k in first_item._asdict().keys() if k != dt_attr]
    for o in res:
        print(datetime.fromtimestamp(getattr(o, dt_attr).timestamp()), end="\t")
        print("\t".join([str(getattr(o, a)) for a in other_attrs]))
