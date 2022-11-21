from typing import List, NamedTuple, Type, Callable, Any, Optional
from datetime import datetime

import more_itertools


def namedtuple_extract_from_annotation(nt: Type[NamedTuple], _type: Any) -> str:
    """
    >>> from typing import NamedTuple; from datetime import datetime
    >>> class Test(NamedTuple): something: datetime
    >>> namedtuple_extract_from_annotation(Test, datetime)
    'something'
    """
    import inspect
    from autotui.typehelpers import resolve_annotation_single

    for attr_name, param in inspect.signature(nt).parameters.items():
        # Optional[(<class 'int'>, False)]
        attr_type, _ = resolve_annotation_single(param.annotation)

        if attr_type == _type:
            return attr_name
    raise TypeError(f"Could not find {_type} on {nt}")


def _extract_dt_from(nt: Type[NamedTuple]) -> Callable[[NamedTuple], datetime]:
    # returns a function, when which given an item of this
    # type, returns the datetime value
    dt_attr: str = namedtuple_extract_from_annotation(nt, datetime)
    return lambda o: getattr(o, dt_attr)  # type: ignore[no-any-return]


def glob_namedtuple_by_datetime(
    nt: Type[NamedTuple], reverse: bool = False
) -> List[NamedTuple]:
    from .autotui_ext import glob_namedtuple

    return sorted(glob_namedtuple(nt), key=_extract_dt_from(nt), reverse=reverse)


def query_recent(nt: Type[NamedTuple], count: int) -> List[NamedTuple]:
    """query the module for recent entries (based on datetime) from a namedtuple"""
    items: List[NamedTuple] = more_itertools.take(
        count, glob_namedtuple_by_datetime(nt, reverse=True)
    )
    return items


def query_print(
    nt: Type[NamedTuple],
    count: int,
    remove_attrs: List[str],
    cached_data: Optional[List[NamedTuple]] = None,
) -> None:
    # assumes that there is a datetime attribute on this, else
    # we have nothing to sort by
    if cached_data is None:
        res = more_itertools.peekable(iter(query_recent(nt, count)))
    else:
        res = more_itertools.peekable(more_itertools.take(count, cached_data))
    try:
        first_item: NamedTuple = res.peek()  # namedtuple-like
    except StopIteration:
        raise RuntimeError(f"data queried from {nt} was empty")
    dt_attr: str = namedtuple_extract_from_annotation(first_item.__class__, datetime)
    # get non-datetime attr names, if they're not filtered
    other_attrs: List[str] = [
        k for k in first_item._asdict().keys() if k != dt_attr and k not in remove_attrs
    ]
    for o in res:
        print(datetime.fromtimestamp(getattr(o, dt_attr).timestamp()), end="\t")
        print(" \t".join([str(getattr(o, a)) for a in other_attrs]))
