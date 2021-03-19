import sys
import inspect

from datetime import datetime
from typing import NamedTuple, Any

# if you define a datetime on a model, the attribute name should be 'when'


class Shower(NamedTuple):
    when: datetime


class Weight(NamedTuple):
    when: datetime
    pounds: float


class Water(NamedTuple):
    when: datetime
    glasses: float


def _class_defined_in_module(o: Any) -> bool:
    return inspect.isclass(o) and o.__module__ == __name__


# dynamically create a list of each of these
MODELS = {
    name.casefold(): klass
    for name, klass in inspect.getmembers(
        sys.modules[__name__], _class_defined_in_module
    )
}
