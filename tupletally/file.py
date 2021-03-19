import os
import sys
import warnings
import glob
from functools import lru_cache
from typing import List, Optional
from pathlib import Path


OS = sys.platform.casefold()
TUPLETALLY_DATA_DIR: str = os.environ.get("TUPLETALLY_DATA_DIR", "~/data/tupletally")


@lru_cache(1)
def tupletally_abs() -> Path:
    p = Path(TUPLETALLY_DATA_DIR).expanduser().absolute()
    if not p.exists():
        warnings.warn(f"{p} does not exist, creating...")
        p.mkdir()
    return p


# creates unique datafiles for each platform
def datafile(for_function: str) -> Path:
    unique_path = f"{for_function}-{OS}.json"
    return tupletally_abs() / unique_path


# globs all datafiles for some for_function
def glob_datafiles(for_function: str, in_dir: Optional[Path] = None) -> List[Path]:
    d: Path = Path(in_dir or tupletally_abs()).absolute()
    return list(map(Path, glob.glob(str(d / f"{for_function}*.json"))))
