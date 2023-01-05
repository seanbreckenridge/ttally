# hook to load information from tally configuration

import sys
import importlib.util
from typing import Callable, Set, Any

from .default_config import ttally_config_path, URL


LOADED: Set[str] = set()


def _load_config_module(
    file: str, module_name: str, test_import_func: Callable[[], None]
) -> Any:
    if module_name in LOADED:
        return sys.modules[module_name]

    # reload?
    if module_name in sys.modules:
        del sys.modules[module_name]

    try:
        spec = importlib.util.spec_from_file_location(module_name, file)
        assert spec is not None
        mod = importlib.util.module_from_spec(spec)
        assert (
            spec.loader is not None
        ), "Error importing configuration, must be on python3.5+?"
        spec.loader.exec_module(mod)
        if module_name not in sys.modules:
            sys.modules[module_name] = mod

        # make sure its importable
        test_import_func()
        LOADED.add(module_name)
        return mod
    except ImportError as e:
        raise ImportError(
            f"""Importing '{module_name}' from '{file}' failed! (error: {e}).
See {URL} for more information"""
        )


def setup_ttally_config() -> None:
    def _test_import() -> None:
        import ttally.config  # noqa

    _load_config_module(ttally_config_path, "ttally.config", _test_import)


setup_ttally_config()
del setup_ttally_config
