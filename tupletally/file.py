import os
import sys
import warnings
import glob
import socket
from datetime import datetime
from functools import lru_cache

from typing import List, Optional
from pathlib import Path


OS = sys.platform.casefold()
# for why this uses socket:
# https://docs.python.org/3/library/os.html#os.uname
HOSTNAME = "".join(socket.gethostname().split()).casefold()
TIMESTAMP = datetime.strftime(datetime.now(), "%Y-%m")
ENV = "TUPLETALLY_DATA_DIR"
DEFAULT_DATA = "~/.local/share/tupletally"


@lru_cache(1)
def tupletally_abs() -> Path:
    ddir: str = os.environ.get(ENV, DEFAULT_DATA)
    p = Path(ddir).expanduser().absolute()
    if not p.exists():
        warnings.warn(f"{p} does not exist, creating...")
        p.mkdir()
    return p


# creates unique datafiles for each platform
def datafile(for_function: str, in_dir: Optional[Path] = None) -> Path:
    # add some OS/platform specific code to this, to prevent
    # conflicts across computers while using syncthing
    # this also decreases the amount of items that have
    # to be loaded into memory for load_prompt_and_writeback
    unique_path = f"{for_function}-{OS}-{HOSTNAME}-{TIMESTAMP}.json"
    return Path(in_dir or tupletally_abs()).absolute() / unique_path


# globs all datafiles for some for_function
def glob_datafiles(for_function: str, in_dir: Optional[Path] = None) -> List[Path]:
    d: Path = Path(in_dir or tupletally_abs()).absolute()
    return list(map(Path, glob.glob(str(d / f"{for_function}*.json"))))
