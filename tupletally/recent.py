from typing import Iterator, Any, List
from datetime import datetime

import more_itertools

from .autotui_ext import glob_namedtuple, namedtuple_extract_from_annotation
from .models import MODELS


def query_recent(for_function: str, count: int) -> Iterator[Any]:
    """query the module for recent entries (based on datetime) from a namedtuple"""
    try:
        nt: Any = MODELS[for_function]
    except KeyError:
        raise RuntimeError(f"Couldn't find model that matches {for_function}")
    dt_attr: str = namedtuple_extract_from_annotation(nt, datetime)
    yield from more_itertools.take(
        count, sorted(glob_namedtuple(nt), key=lambda p: getattr(p, dt_attr), reverse=True)  # type: ignore[no-any-return]
    )


def query_print(for_function: str, count: int = 10) -> None:
    # assumes that there is a datetime attribute on this, else
    # we have nothing to sort by
    res: Iterator[Any] = query_recent(for_function, count)
    res = more_itertools.peekable(res)
    first_item = res.peek()  # namedtuple-like
    dt_attr: str = namedtuple_extract_from_annotation(first_item.__class__, datetime)
    # get non-datetime attr names
    other_attrs: List[str] = [k for k in first_item._asdict().keys() if k != dt_attr]
    for o in res:
        print(datetime.fromtimestamp(getattr(o, dt_attr).timestamp()), end="\t")
        print("\t".join([str(getattr(o, a)) for a in other_attrs]))
