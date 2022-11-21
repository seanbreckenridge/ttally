import os
import json
from pathlib import Path
from typing import Dict, Optional, Set, Any, NamedTuple, Iterator, List
import shelve

from .models import MODELS

cache_dir = Path(os.environ.get("XDG_CACHE_DIR", str(Path.home() / ".cache")))


def ttally_cache_dir() -> Path:
    ttally_cache_dir = cache_dir / "ttally"
    if not ttally_cache_dir.exists():
        ttally_cache_dir.mkdir(parents=True)
    return ttally_cache_dir


cdir = ttally_cache_dir()
hash_file = str(cdir / "ttally_hash.pickle")


def file_hash(model: str) -> str:
    """
    A unique representation of the current files/timestamp for a model
    """
    from .file import glob_datafiles

    files = list(glob_datafiles(model))
    files_stat = [(f, f.stat().st_mtime) for f in files]
    files_stat.sort(key=lambda t: t[1])
    return "|".join(f"{f}:{st}" for (f, st) in files_stat)


FileHashes = Dict[str, str]


def file_hashes(for_models: Optional[Set[str]] = None) -> FileHashes:
    if for_models:
        return {model: file_hash(model) for model in MODELS if model in for_models}
    else:
        return {model: file_hash(model) for model in MODELS}


def cache_is_stale(
    hashes: Optional[FileHashes] = None, for_models: Optional[Set[str]] = None
) -> bool:

    cache_stale = False

    with shelve.open(hash_file) as db:
        fh = hashes or file_hashes()
        db_hashes: FileHashes = db.get("hash", {})
        for model, current_hash in fh.items():
            if for_models and model not in for_models:
                continue
            if current_hash != db_hashes.get(model):
                cache_stale = True
                break

    return cache_stale


def save_hashes(hashes: Optional[FileHashes] = None) -> None:
    with shelve.open(hash_file) as db:
        db["hash"] = hashes or file_hashes()


def cache_sorted_exports() -> bool:

    fh = file_hashes()
    cache_stale = cache_is_stale(fh)

    if cache_stale:
        from .recent import glob_namedtuple_by_datetime
        from autotui.fileio import namedtuple_sequence_dumps

        all_data = {
            model_name: namedtuple_sequence_dumps(
                glob_namedtuple_by_datetime(model_type, reverse=False), indent=""
            )
            for model_name, model_type in MODELS.items()
        }

        for model, model_data in all_data.items():
            with open(cdir / f"{model}-cache.json", "w") as f:
                f.write(model_data)

        save_hashes(fh)
    return cache_stale


def read_cache_str(model: str) -> str:
    fh = file_hashes(for_models={model})
    if cache_is_stale(hashes=fh, for_models={model}):
        raise RuntimeError("Cache is Stale")
    cache_file = cdir / f"{model}-cache.json"
    if not cache_file.exists():
        raise RuntimeError("Cache file does not exist")
    return cache_file.read_text()


def _load_json(nt_string: str) -> Any:
    try:
        # speedup load if orjson is installed
        import orjson  # type: ignore[import]

        return orjson.loads(nt_string)
    except ImportError:
        pass
    return json.loads(nt_string)


def read_cache_json(model: str) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = _load_json(read_cache_str(model))
    return data
