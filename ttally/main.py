import sys
import json
from typing import NamedTuple, Type, Optional, List, Sequence, Iterable, Any

import click

from .accessor import Accessor


def wrap_accessor(*, accessor: Accessor) -> click.Group:
    @click.group()
    def call_main() -> None:
        """
        Tally things that I do often!

        Given a few namedtuples, this creates serializers/deserializers
        and an interactive interface using 'autotui', and aliases
        to:

        prompt using default autotui behavior, writing to the ttally datafile,
        same as above, but if the model has a datetime, set it to now,
        query the 10 most recent items for a model
        """
        pass

    @call_main.command(short_help="generate shell aliases")
    def generate() -> None:
        """
        Generate the shell aliases!
        """
        for a in accessor.generate_shell_aliases():
            print(a)

    def _model_complete(
        ctx: click.Context, args: Sequence[str], incomplete: str
    ) -> List[str]:
        return [
            m for m in accessor._autocomplete_model_names() if m.startswith(incomplete)
        ]

    model_with_completion = click.argument("MODEL", shell_complete=_model_complete)

    @call_main.command(short_help="add item by piping JSON")
    @model_with_completion
    @click.option(
        "-p",
        "--partial",
        default=False,
        is_flag=True,
        help="Allow partial input -- prompt any fields which arent provided",
    )
    @click.option(
        "-f",
        "--file",
        default=None,
        type=click.Path(exists=True),
        help="Read from file instead of STDIN",
    )
    def from_json(model: str, partial: bool, file: Optional[str]) -> None:
        """
        A way to allow external programs to save JSON data to the current file for the model

        Provide a list of JSON from STDIN, and the corresponding model to parse it to
        (in lowercase) as the first argument, and this parses (validates)
        and saves it to the file
        """

        if file is None:
            accessor.save_from(
                accessor._model_from_string(model), use_input=sys.stdin, partial=partial
            )
        else:
            with open(file, "r") as f:
                accessor.save_from(
                    accessor._model_from_string(model), use_input=f, partial=partial
                )

    @call_main.command(short_help="print the datafile location")
    @model_with_completion
    def datafile(model: str) -> None:
        """
        Print the location of the current datafile for some model
        """
        accessor._model_from_string(model)
        f = accessor.datafile(model)
        if not f.exists():
            click.secho(f"Warning: {f} doesn't exist", err=True, fg="red")
        click.echo(f)

    @call_main.command(name="prompt", help="tally an item")
    @model_with_completion
    def _prompt(model: str) -> None:
        """
        Prompt for every field in the given model
        """
        accessor.prompt(accessor._model_from_string(model))

    @call_main.command(name="models", help="list models")
    def _models_cmd() -> None:
        """
        List all ttally models
        """
        click.echo("\n".join(accessor._autocomplete_model_names()))

    @call_main.command(name="prompt-now", help="tally an item (now)")
    @model_with_completion
    def _prompt_now(model: str) -> None:
        """
        Prompt for every field in the model, except datetime, which should default to now
        """
        accessor.prompt_now(accessor._model_from_string(model))

    @call_main.command(name="recent", short_help="print recently tallied items")
    @model_with_completion
    @click.option(
        "-r",
        "--remove-attrs",
        type=str,
        default="",
        help="comma separated list of attributes to remove while printing",
    )
    @click.argument("COUNT", type=int, default=10)
    def _recent(model: str, remove_attrs: str, count: int) -> None:
        """
        List recent items logged for this model
        """
        from more_itertools import take, always_reversible

        res: Optional[List[NamedTuple]] = None
        try:
            # reverse so it is ordered for query properly
            from autotui.serialize import deserialize_namedtuple

            res = [
                deserialize_namedtuple(o, to=accessor.MODELS[model])
                for o in take(
                    count, always_reversible(accessor.read_cache_json(model=model))
                )
            ]
        except RuntimeError:
            pass

        attrs = [a.strip() for a in remove_attrs.split(",") if a.strip()]
        accessor.query_print(
            accessor._model_from_string(model),
            count,
            remove_attrs=attrs,
            cached_data=res,
        )

    @call_main.command(short_help="export all data from a model")
    @model_with_completion
    @click.option(
        "-s",
        "--stream",
        default=False,
        is_flag=True,
        help="Stream objects as they're read, instead of a list",
    )
    def export(model: str, stream: bool) -> None:
        """
        List all the data from a model as JSON
        """

        # read from cache if cache isnt stale
        itr: Optional[Iterable[Any]] = None
        try:
            itr = accessor.read_cache_json(model=model)
        except RuntimeError:
            pass

        # cache was stale, read from datafiles
        if itr is None:
            from autotui.fileio import namedtuple_sequence_dumps

            itr = json.loads(
                namedtuple_sequence_dumps(
                    list(accessor.glob_namedtuple(accessor._model_from_string(model)))
                )
            )

        assert itr is not None

        if stream:
            for blob in itr:
                sys.stdout.write(json.dumps(blob))
                sys.stdout.write("\n")
        else:
            sys.stdout.write(json.dumps(list(itr)))
            sys.stdout.write("\n")
        sys.stdout.flush()

    @call_main.command(short_help="merge all data for a model into one file")
    @model_with_completion
    @click.option(
        "--sort-key", default=None, help="Sort resulting merged data by JSON key"
    )
    def merge(model: str, sort_key: Optional[str]) -> None:
        """
        Merge all datafiles for one model into a single '-merged.json' file
        """
        from pathlib import Path
        from datetime import datetime

        from autotui.fileio import namedtuple_sequence_dumps

        datafiles: List[Path] = list(accessor.glob_datafiles(model))
        if len(datafiles) == 0:
            click.echo(f"No datafiles for model {model}", err=True)
            return

        data = json.loads(
            namedtuple_sequence_dumps(
                list(accessor.glob_namedtuple(accessor._model_from_string(model)))
            )
        )

        # if provided, use sort key
        if sort_key is not None and len(data) > 0:
            assert sort_key in data[0], f"Could not find {sort_key} in {data[0]}"
            data = list(sorted(data, key=lambda obj: obj[sort_key]))  # type: ignore[no-any-return]

        epoch = int(datetime.now().timestamp())
        cachefile = accessor.ttally_temp_dir() / f"{model}-{epoch}-merged.json"

        click.echo(f"Writing backup to '{cachefile}'", err=True)
        with cachefile.open("w") as backup_f:
            json.dump(data, backup_f)

        # remove current datafiles
        for rmf in datafiles:
            click.echo(f"Removing '{rmf}'", err=True)
            rmf.unlink()

        merge_target = accessor.ttally_merged_path(model)
        with merge_target.open("w") as merged_f:
            json.dump(data, merged_f)

        click.echo(f"Wrote merged file to '{merge_target}'", err=True)

    @call_main.command(short_help="cache export data", name="update-cache")
    @click.option(
        "--print-hashes",
        is_flag=True,
        default=False,
        help="print current filehash debug info",
    )
    def update_cache(print_hashes: bool) -> None:
        """
        Caches data for 'export' and 'recent' by saving
        the current data and an index to ~/.cache/ttally

        exit code 0 if cache was updated, 2 if it was already up to date
        """
        was_stale = accessor.cache_sorted_exports()
        ret = 0
        if was_stale:
            click.echo("Cache was stale, updated", err=True)
        else:
            click.echo("Cache is already up to date", err=True)
            ret = 2
        if print_hashes:
            click.echo(json.dumps(accessor.file_hashes()))
        sys.exit(ret)

    @call_main.command(short_help="edit the datafile")
    @model_with_completion
    def edit(model: str) -> None:
        """
        Edit the current datafile with your editor
        """
        accessor._model_from_string(model)
        f = accessor.datafile(model)
        if not f.exists():
            click.secho(f"Warning: {f} doesn't exist. ", err=True, fg="red")
            if not click.confirm("Open anyways?"):
                return

        click.edit(filename=str(f))

    return call_main
