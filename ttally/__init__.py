# hook to load information from tally configuration

import os
import sys
import warnings
import importlib.util
from pathlib import Path

URL = "https://github.com/seanbreckenridge/ttally"


def get_conf_file() -> Path:
    cfg_file: str = os.environ.get("TTALLY_CFG", "~/.config/ttally.py")
    cfg_path = Path(cfg_file).expanduser().absolute()
    if not cfg_path.parent.exists():
        warnings.warn("Directory for configuration doesn't exist, creating...")
        cfg_path.parent.mkdir()
    if not cfg_path.exists():
        raise FileNotFoundError(
            f"Expected configuration to exist at {cfg_path}, see {URL} for an example"
        )
    return cfg_path


def setup_config() -> None:
    conf: Path = get_conf_file()
    sconf: str = str(conf)

    mname = "ttally.config"
    # redirect import
    if mname in sys.modules:
        del sys.modules[mname]
    try:
        spec = importlib.util.spec_from_file_location(mname, sconf)
        assert spec is not None
        mod = importlib.util.module_from_spec(spec)
        err = "Error importing configuration, must be on python3.5+?"
        assert spec.loader is not None, err
        # not sure why mypy is using the legacy (<3.4) types here?
        # https://docs.python.org/3/library/importlib.html#importlib.abc.Loader
        spec.loader.exec_module(mod)  # type: ignore[attr-defined]
        if mname not in sys.modules:
            sys.modules[mname] = mod
        # make sure its importable
        import ttally.config  # noqa
    except ImportError as e:
        raise ImportError(
            f"""
Importing 'ttally.config' failed! (error: {e}).
This file is typically located at  ~/.config/ttally.py, see {URL} for
more information
"""
        )


setup_config()
del setup_config
