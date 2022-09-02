import os
import sys
from functools import lru_cache
from pathlib import Path
from tempfile import gettempdir
from typing import Optional, Iterator


ENV = "TTALLY_DATA_DIR"
DEFAULT_DATA = "~/.local/share/ttally"


@lru_cache(1)
def versioned_timestamp() -> str:
    import socket
    from datetime import datetime

    OS = sys.platform.casefold()
    # for why this uses socket:
    # https://docs.python.org/3/library/os.html#os.uname
    HOSTNAME = "".join(socket.gethostname().split()).casefold()
    TIMESTAMP = datetime.strftime(datetime.now(), "%Y-%m")
    return f"{OS}-{HOSTNAME}-{TIMESTAMP}"


@lru_cache(1)
def ttally_abs() -> Path:
    ddir: str = os.environ.get(ENV, DEFAULT_DATA)
    p = Path(ddir).expanduser().absolute()
    if not p.exists():
        import warnings

        warnings.warn(f"{p} does not exist, creating...")
        p.mkdir()
    return p


def ttally_merged_path(model: str) -> Path:
    return ttally_abs() / f"{model}-merged.json"


# creates unique datafiles for each platform
def datafile(for_function: str, in_dir: Optional[Path] = None) -> Path:
    # add some OS/platform specific code to this, to prevent
    # conflicts across computers while using syncthing
    # this also decreases the amount of items that have
    # to be loaded into memory for load_prompt_and_writeback
    ext = os.environ.get("TTALLY_EXT", "yaml")
    u = f"{for_function}-{versioned_timestamp()}.{ext}"
    return Path(in_dir or ttally_abs()).absolute() / u


# globs all datafiles for some for_function
def glob_datafiles(for_function: str, in_dir: Optional[Path] = None) -> Iterator[Path]:
    d: Path = Path(in_dir or ttally_abs()).absolute()
    for f in os.listdir(d):
        if f.startswith(for_function):
            yield d / f


def ttally_cache_dir() -> Path:
    cache_dir = Path(os.environ.get("XDG_CACHE_DIR", str(Path.home() / ".cache")))
    ttally_cache_dir = cache_dir / "ttally"
    if not ttally_cache_dir.exists():
        ttally_cache_dir.mkdir(parents=True)
    return ttally_cache_dir


def ttally_temp_dir() -> Path:
    tdir = gettempdir()
    ttally_temp_dir = Path(tdir) / "ttally"
    if not ttally_temp_dir.exists():
        ttally_temp_dir.mkdir(parents=True)
    return ttally_temp_dir
