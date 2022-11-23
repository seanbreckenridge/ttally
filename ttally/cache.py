import os
import json
from pathlib import Path
from functools import lru_cache
from typing import Dict, Optional, Set, Any, List, Type, NamedTuple
import shelve

from .models import MODELS

base_cache_dir = Path(os.environ.get("XDG_CACHE_DIR", str(Path.home() / ".cache")))


def ttally_cache_dir() -> Path:
    ttally_cache_dir = Path(
        os.environ.get("TTALLY_CACHE_DIR", base_cache_dir / "ttally")
    )
    if not ttally_cache_dir.exists():
        ttally_cache_dir.mkdir(parents=True)
    return ttally_cache_dir


default_cdir = ttally_cache_dir()


def file_hash(*, model: str, data_dir: Optional[Path] = None) -> str:
    """
    A unique representation of the current files/timestamp for a model
    """
    from .file import glob_datafiles

    files = list(glob_datafiles(model, data_dir=data_dir))
    files_stat = [(f, f.stat().st_mtime) for f in files]
    files_stat.sort(key=lambda t: t[1])
    return "|".join(f"{f}:{st}" for (f, st) in files_stat)


FileHashes = Dict[str, str]


def file_hashes(
    *,
    models: Optional[Dict[str, Type[NamedTuple]]] = None,
    data_dir: Optional[Path] = None,
    for_models: Optional[Set[str]] = None,
) -> FileHashes:
    if models is None:
        models = MODELS
    if for_models:
        return {
            model: file_hash(model=model, data_dir=data_dir)
            for model in models
            if model in for_models
        }
    else:
        return {model: file_hash(model=model, data_dir=data_dir) for model in models}


def cache_is_stale(
    *,
    hashes: Optional[FileHashes] = None,
    for_models: Optional[Set[str]] = None,
    models: Optional[Dict[str, Type[NamedTuple]]] = None,
    data_dir: Optional[Path] = None,
    cache_dir: Optional[Path] = None,
) -> bool:

    cache_stale = False
    if models is None:
        models = MODELS

    with shelve.open(hash_file(cache_dir=cache_dir)) as db:
        fh = hashes or file_hashes(
            for_models=for_models, models=models, data_dir=data_dir
        )
        db_hashes: FileHashes = db.get("hash", {})
        for model, current_hash in fh.items():
            if for_models and model not in for_models:
                continue
            if current_hash != db_hashes.get(model):
                cache_stale = True
                break

    return cache_stale


@lru_cache(maxsize=None)
def hash_file(cache_dir: Optional[Path] = None) -> str:
    cdir = cache_dir if cache_dir is not None else default_cdir
    return str(cdir / "ttally_hash.pickle")


def save_hashes(
    *,
    hashes: Optional[FileHashes] = None,
    models: Optional[Dict[str, Type[NamedTuple]]] = None,
    cache_dir: Optional[Path] = None,
    data_dir: Optional[Path] = None,
) -> None:
    cdir = cache_dir if cache_dir is not None else default_cdir
    with shelve.open(hash_file(cache_dir=cdir)) as db:
        db["hash"] = hashes or file_hashes(models=models, data_dir=data_dir)


def cache_sorted_exports(
    *,
    models: Optional[Dict[str, Type[NamedTuple]]] = None,
    data_dir: Optional[Path] = None,
    cache_dir: Optional[Path] = None,
) -> bool:

    if models is None:
        models = MODELS

    fh = file_hashes(models=models, data_dir=data_dir)
    cache_stale = cache_is_stale(
        hashes=fh, models=models, data_dir=data_dir, cache_dir=cache_dir
    )

    if cache_stale:
        from .recent import glob_namedtuple_by_datetime
        from autotui.fileio import namedtuple_sequence_dumps

        cdir = cache_dir if cache_dir is not None else default_cdir

        all_data = {
            model_name: namedtuple_sequence_dumps(
                glob_namedtuple_by_datetime(
                    model_type, reverse=False, data_dir=data_dir
                ),
                indent=None,
            )
            for model_name, model_type in models.items()
        }

        for model, model_data in all_data.items():
            with open(cdir / f"{model}-cache.json", "w") as f:
                f.write(model_data)

        save_hashes(hashes=fh, models=models, cache_dir=cache_dir, data_dir=data_dir)
    return cache_stale


def read_cache_str(
    *,
    model: str,
    models: Optional[Dict[str, Type[NamedTuple]]] = None,
    data_dir: Optional[Path] = None,
    cache_dir: Optional[Path] = None,
) -> str:
    cdir = cache_dir if cache_dir is not None else default_cdir
    fh = file_hashes(for_models={model}, models=models, data_dir=data_dir)
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


def read_cache_json(
    *,
    model: str,
    models: Optional[Dict[str, Type[NamedTuple]]] = None,
    data_dir: Optional[Path] = None,
    cache_dir: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = _load_json(
        read_cache_str(
            model=model, models=models, data_dir=data_dir, cache_dir=cache_dir
        )
    )
    return data
