from typing import Iterator, Any
import pprint

import more_itertools

from .autotui_ext import glob_namedtuple
from .models import MODELS

# query the module for recent entries from a namedtuple
def query_recent(for_function: str, count: int) -> Iterator[Any]:
    try:
        nt: Any = MODELS[for_function]
    except KeyError:
        raise RuntimeError(f"Couldn't find model that matches {for_function}")
    yield from more_itertools.take(
        count, sorted(glob_namedtuple(nt), key=lambda p: p.when, reverse=True)  # type: ignore[no-any-return]
    )


def query_print(for_function: str, count: int = 10) -> None:
    pprint.pprint(list(query_recent(for_function, count)))
