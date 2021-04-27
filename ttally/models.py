import inspect

from typing import Any, Dict, NamedTuple, Type

# should already be configured, since __init__.py hook runs
# when the module is initially loaded

from ttally import config


def _is_model(o: Any) -> bool:
    return inspect.isclass(o) and issubclass(o, tuple) and hasattr(o, "_fields")


# dynamically create a list of each of these
MODELS: Dict[str, Type[NamedTuple]] = {
    name.casefold(): klass for name, klass in inspect.getmembers(config, _is_model)
}
