"""
Encapsulates all interaction with ttally under a class, so its easier to extend
"""

import sys
import os
import json
import shelve
import inspect
from functools import lru_cache
from pathlib import Path
from typing import (
    Set,
    Callable,
    TYPE_CHECKING,
    Iterator,
    cast,
    Any,
    NamedTuple,
    Optional,
    Type,
    List,
    Dict,
    TextIO,
)
from datetime import datetime

FileHashes = Dict[str, str]


if TYPE_CHECKING:
    from autotui.fileio import Format
    from click import Group


class Accessor:
    def __init__(
        self,
        *,
        name: str,
        module_name: str,
        config_file: str,
        data_dir: Optional[str] = None,
        data_dir_environment_variable: str = "TTALLY_DATA_DIR",
        data_dir_default: str = "~/.local/share/ttally",
        merged_extesion: "Format" = "json",
        extension: Optional["Format"] = None,
    ) -> None:

        # config
        self.name = name
        self.module_name = module_name
        self.config_file = config_file
        self.extension: Optional["Format"] = extension

        # extensions
        if extension is None and "TTALLY_EXT" in os.environ:
            self.extension = cast("Format", os.environ["TTALLY_EXT"])
        self.merged_extension = merged_extesion

        # load config
        self.config_module = self.import_config()
        assert (
            self.config_module is not None
        ), f"{self.config_module} failed to import from {self.config_file}"

        # compute data/cache directories
        if data_dir is None:
            self.data_dir: Path = self.compute_data_dir(
                data_dir_environment_variable, data_dir_default
            )
        else:
            self.data_dir = Path(data_dir)
        self.cache_dir = self.compute_cache_dir()
        self.hash_file = str(self.cache_dir / "ttally_hash.pickle")

        self.MODELS: Dict[str, Type[NamedTuple]] = {
            name.casefold(): klass
            for name, klass in inspect.getmembers(
                self.config_module, self.__class__._is_model
            )
        }

    # CONFIG

    def import_config(self) -> Any:
        from ttally import _load_config_module

        return _load_config_module(
            self.config_file, self.module_name, self.check_import
        )

    def check_import(self) -> None:
        import ttally.config  # noqa

    @staticmethod
    def _is_model(o: Any) -> bool:
        return inspect.isclass(o) and issubclass(o, tuple) and hasattr(o, "_fields")

    # AUTOTUI_EXT

    @staticmethod
    def namedtuple_func_name(nt: Type[NamedTuple]) -> str:
        assert hasattr(nt, "_fields"), "Did not receive a valid NamedTuple!"
        return str(nt.__name__.casefold())

    # load, prompt and writeback one of the models
    def prompt(self, nt: Type[NamedTuple]) -> None:

        from autotui.shortcuts import load_prompt_and_writeback

        f: Path = self.datafile(self.namedtuple_func_name(nt))
        load_prompt_and_writeback(nt, f)

    # prompt, but set the datetime for the resulting nametuple to now
    def prompt_now(self, nt: Type[NamedTuple]) -> None:
        from autotui.shortcuts import load_prompt_and_writeback

        # load items from file
        p: Path = self.datafile(self.namedtuple_func_name(nt))
        load_prompt_and_writeback(nt, p, type_use_values={datetime: datetime.now})

    # takes one of the models.py and loads all data from it
    def glob_namedtuple(self, nt: Type[NamedTuple]) -> Iterator[NamedTuple]:

        from autotui.shortcuts import load_from
        from itertools import chain

        yield from chain(
            *map(
                lambda p: load_from(nt, p, allow_empty=True),
                self.glob_datafiles(self.namedtuple_func_name(nt)),
            )
        )

    # used in __main__.py for the from_json command
    def save_from(
        self, nt: Type[NamedTuple], use_input: TextIO, partial: bool = False
    ) -> None:
        from autotui.namedtuple_prompt import prompt_namedtuple
        from autotui.fileio import namedtuple_sequence_loads
        from autotui.shortcuts import load_from, dump_to

        json_text: str = use_input.read()
        p = self.datafile(self.namedtuple_func_name(nt))
        items: List[NamedTuple] = load_from(nt, p, allow_empty=True)
        new_items: List[NamedTuple] = []
        if partial:
            # load the list as json blobs
            os.environ["AUTOTUI_DISABLE_WARNINGS"] = "1"  # ignore null warnings
            blobs: List[Dict[str, Any]] = []
            for b in namedtuple_sequence_loads(json_text, nt):
                blobs.append({k: v for k, v in b._asdict().items() if v is not None})
            del os.environ["AUTOTUI_DISABLE_WARNINGS"]
            for bd in blobs:
                new_nt = prompt_namedtuple(nt, attr_use_values=bd)
                new_items.append(new_nt)
        else:
            new_items.extend(namedtuple_sequence_loads(json_text, nt))
        items.extend(new_items)
        dump_to(items, p)

    # FILE/IO

    @classmethod
    @lru_cache(maxsize=1)
    def versioned_timestamp(cls) -> str:
        import socket

        OS = sys.platform.casefold()
        # for why this uses socket:
        # https://docs.python.org/3/library/os.html#os.uname
        HOSTNAME = "".join(socket.gethostname().split()).casefold()
        TIMESTAMP = datetime.strftime(datetime.now(), "%Y-%m")
        return f"{OS}-{HOSTNAME}-{TIMESTAMP}"

    def compute_data_dir(
        self, environment_variable: str, data_dir_default: str
    ) -> Path:
        ddir: str = os.environ.get(environment_variable, data_dir_default)
        p = Path(ddir).expanduser().absolute()
        if not p.exists():
            import warnings

            warnings.warn(f"{p} does not exist, creating...")
            p.mkdir()
        return p

    def ttally_merged_path(self, model: str) -> Path:
        return self.data_dir / f"{model}-merged.{self.merged_extension}"

    # creates unique datafiles for each platform
    def datafile(self, for_function: str) -> Path:
        # add some OS/platform specific code to this, to prevent
        # conflicts across computers while using syncthing
        # this also decreases the amount of items that have
        # to be loaded into memory for load_prompt_and_writeback
        ext = os.environ.get("TTALLY_EXT", "yaml")
        return self.data_dir / f"{for_function}-{self.versioned_timestamp()}.{ext}"

    # globs all datafiles for some for_function
    def glob_datafiles(self, for_function: str) -> Iterator[Path]:
        for f in os.listdir(self.data_dir):
            if f.startswith(for_function):
                yield self.data_dir / f

    def ttally_temp_dir(self) -> Path:
        from tempfile import gettempdir

        tdir = gettempdir()
        ttally_temp_dir = Path(tdir) / self.name
        if not ttally_temp_dir.exists():
            ttally_temp_dir.mkdir(parents=True)
        return ttally_temp_dir

    # FUNCS

    def funccreator(self) -> Callable[[str], Callable[[], Iterator[NamedTuple]]]:
        def model_iterator(name: str) -> Callable[[], Iterator[NamedTuple]]:
            if name in self.MODELS:
                return lambda: self.glob_namedtuple(self.MODELS[name])
            raise AttributeError(f"No such attribute {name}")

        return model_iterator

    # CODEGEN

    def generate_shell_aliases(self, python_loc: str = "python3") -> Iterator[str]:
        pre = f"'{python_loc} -m ttally "
        suf = "'"
        for mname in self.MODELS.keys():
            yield f"alias {mname}={pre}prompt {mname}{suf}"
            yield f"alias {mname}-now={pre}prompt-now {mname}{suf}"
            yield f"alias {mname}-recent={pre}recent {mname}{suf}"

    # RECENT
    @classmethod
    def namedtuple_extract_from_annotation(
        cls, nt: Type[NamedTuple], _type: Any
    ) -> str:
        """
        >>> from typing import NamedTuple; from datetime import datetime
        >>> class Test(NamedTuple): something: datetime
        >>> namedtuple_extract_from_annotation(Test, datetime)
        'something'
        """
        import inspect
        from autotui.typehelpers import resolve_annotation_single

        for attr_name, param in inspect.signature(nt).parameters.items():
            # Optional[(<class 'int'>, False)]
            attr_type, _ = resolve_annotation_single(param.annotation)

            if attr_type == _type:
                return attr_name
        raise TypeError(f"Could not find {_type} on {nt}")

    @classmethod
    def _extract_dt_from(cls, nt: Type[NamedTuple]) -> Callable[[NamedTuple], datetime]:
        # returns a function, when which given an item of this
        # type, returns the datetime value
        dt_attr: str = cls.namedtuple_extract_from_annotation(nt, datetime)
        return lambda o: getattr(o, dt_attr)  # type: ignore[no-any-return]

    def glob_namedtuple_by_datetime(
        self,
        nt: Type[NamedTuple],
        reverse: bool = False,
    ) -> List[NamedTuple]:
        return sorted(
            self.glob_namedtuple(nt),
            key=self._extract_dt_from(nt),
            reverse=reverse,
        )

    def query_recent(self, nt: Type[NamedTuple], count: int) -> List[NamedTuple]:
        import more_itertools

        """query the module for recent entries (based on datetime) from a namedtuple"""
        items: List[NamedTuple] = more_itertools.take(
            count, self.glob_namedtuple_by_datetime(nt, reverse=True)
        )
        return items

    def query_print(
        self,
        nt: Type[NamedTuple],
        count: int,
        remove_attrs: List[str],
        cached_data: Optional[List[NamedTuple]] = None,
    ) -> None:
        import more_itertools

        # assumes that there is a datetime attribute on this, else
        # we have nothing to sort by
        if cached_data is None:
            res = more_itertools.peekable(iter(self.query_recent(nt, count)))
        else:
            res = more_itertools.peekable(more_itertools.take(count, cached_data))
        try:
            first_item: NamedTuple = res.peek()  # namedtuple-like
        except StopIteration:
            raise RuntimeError(f"data queried from {nt} was empty")
        dt_attr: str = self.namedtuple_extract_from_annotation(
            first_item.__class__, datetime
        )
        # get non-datetime attr names, if they're not filtered
        other_attrs: List[str] = [
            k
            for k in first_item._asdict().keys()
            if k != dt_attr and k not in remove_attrs
        ]
        for o in res:
            print(datetime.fromtimestamp(getattr(o, dt_attr).timestamp()), end="\t")
            print(" \t".join([str(getattr(o, a)) for a in other_attrs]))

    def compute_cache_dir(self) -> Path:
        base_cache_dir = Path(
            os.environ.get("XDG_CACHE_DIR", str(Path.home() / ".cache"))
        )

        ttally_cache_dir = Path(
            os.environ.get("TTALLY_CACHE_DIR", base_cache_dir / "ttally")
        )
        if not ttally_cache_dir.exists():
            ttally_cache_dir.mkdir(parents=True)
        return ttally_cache_dir

    def file_hash(self, *, model: str) -> str:
        """
        A unique representation of the current files/timestamp for a model
        """
        files = list(self.glob_datafiles(model))
        files_stat = [(f, f.stat().st_mtime) for f in files]
        files_stat.sort(key=lambda t: t[1])
        return "|".join(f"{f}:{st}" for (f, st) in files_stat)

    def file_hashes(
        self,
        *,
        models: Optional[Dict[str, Type[NamedTuple]]] = None,
        for_models: Optional[Set[str]] = None,
    ) -> FileHashes:
        if models is None:
            models = self.MODELS
        if for_models:
            return {
                model: self.file_hash(model=model)
                for model in models
                if model in for_models
            }
        else:
            return {model: self.file_hash(model=model) for model in models}

    def cache_is_stale(
        self,
        *,
        hashes: Optional[FileHashes] = None,
        for_models: Optional[Set[str]] = None,
        models: Optional[Dict[str, Type[NamedTuple]]] = None,
    ) -> bool:

        cache_stale = False
        if models is None:
            models = self.MODELS

        with shelve.open(self.hash_file) as db:
            fh = hashes or self.file_hashes(for_models=for_models, models=models)
            db_hashes: FileHashes = db.get("hash", {})
            for model, current_hash in fh.items():
                if for_models and model not in for_models:
                    continue
                if current_hash != db_hashes.get(model):
                    cache_stale = True
                    break

        return cache_stale

    def save_hashes(
        self,
        *,
        hashes: Optional[FileHashes] = None,
        models: Optional[Dict[str, Type[NamedTuple]]] = None,
    ) -> None:
        with shelve.open(self.hash_file) as db:
            db["hash"] = hashes or self.file_hashes(models=models)

    def cache_sorted_exports(
        self,
        *,
        models: Optional[Dict[str, Type[NamedTuple]]] = None,
    ) -> bool:

        if models is None:
            models = self.MODELS

        fh = self.file_hashes(models=models)
        cache_stale = self.cache_is_stale(hashes=fh, models=models)

        if cache_stale:
            from autotui.fileio import namedtuple_sequence_dumps

            all_data = {
                model_name: namedtuple_sequence_dumps(
                    self.glob_namedtuple_by_datetime(model_type, reverse=False),
                    indent=None,
                )
                for model_name, model_type in models.items()
            }

            for model, model_data in all_data.items():
                with open(self.cache_dir / f"{model}-cache.json", "w") as f:
                    f.write(model_data)

            self.save_hashes(hashes=fh, models=models)
        return cache_stale

    def read_cache_str(
        self,
        *,
        model: str,
        models: Optional[Dict[str, Type[NamedTuple]]] = None,
    ) -> str:
        fh = self.file_hashes(for_models={model}, models=models)
        if self.cache_is_stale(hashes=fh, for_models={model}):
            raise RuntimeError("Cache is Stale")
        cache_file = self.cache_dir / f"{model}-cache.json"
        if not cache_file.exists():
            raise RuntimeError("Cache file does not exist")
        return cache_file.read_text()

    @classmethod
    def _load_json(cls, nt_string: str) -> Any:
        try:
            # speedup load if orjson is installed
            import orjson  # type: ignore[import]

            return orjson.loads(nt_string)
        except ImportError:
            pass
        return json.loads(nt_string)

    def read_cache_json(
        self,
        *,
        model: str,
        models: Optional[Dict[str, Type[NamedTuple]]] = None,
    ) -> List[Dict[str, Any]]:
        data: List[Dict[str, Any]] = self.__class__._load_json(
            self.read_cache_str(model=model, models=models)
        )
        return data

    # CLI helpers
    def _autocomplete_model_names(self) -> List[str]:
        # sort this, so that the order doesn't change while tabbing through
        return sorted(m for m in self.MODELS)

    def _model_from_string(self, model_name: str) -> Type[NamedTuple]:
        try:
            return self.MODELS[model_name]
        except KeyError:
            import click

            click.echo(
                f"Could not find a model named {model_name}. Known models: {', '.join(self.MODELS)}",
                err=True,
            )
            sys.exit(1)

    def cli_wrap(self, call: bool = True, *args: Any, **kwargs: Any) -> "Group":
        from ttally.main import wrap_accessor

        grp = wrap_accessor(accessor=self)
        if call:
            grp(*args, **kwargs)

        return grp
