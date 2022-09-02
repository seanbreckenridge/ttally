import sys
import json
from typing import NamedTuple, Type, Optional, List, Sequence

import click

from .models import MODELS


def _model_from_string(model_name: str) -> Type[NamedTuple]:
    try:
        return MODELS[model_name]
    except KeyError:
        click.echo(f"Could not find a model named {model_name}", err=True)
        sys.exit(1)


@click.group()
def main() -> None:
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


@main.command(short_help="generate shell aliases")
def generate() -> None:
    """
    Generate the shell aliases!
    """
    from .codegen import generate_shell_aliases

    for a in generate_shell_aliases():
        print(a)


def _model_names() -> List[str]:
    # sort this, so that the order doesn't change while tabbing through
    return sorted(m for m in MODELS)


def _model_complete(
    ctx: click.Context, args: Sequence[str], incomplete: str
) -> List[str]:
    return [m for m in _model_names() if m.startswith(incomplete)]


model_with_completion = click.argument("MODEL", shell_complete=_model_complete)


@main.command(short_help="add item by piping JSON")
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
    from .autotui_ext import save_from

    if file is None:
        save_from(_model_from_string(model), use_input=sys.stdin, partial=partial)
    else:
        with open(file, "r") as f:
            save_from(_model_from_string(model), use_input=f, partial=partial)


@main.command(short_help="print the datafile location")
@model_with_completion
def datafile(model: str) -> None:
    """
    Print the location of the current datafile for some model
    """
    from .file import datafile as df

    m = model.lower()
    assert m in MODELS, f"Couldn't find model {m}"
    f = df(m)
    if not f.exists():
        click.secho(f"Warning: {f} doesn't exist", err=True, fg="red")
    click.echo(f)


@main.command(name="models", help="list models")
def _models_cmd() -> None:
    """
    List all ttally models
    """
    click.echo("\n".join(_model_names()))


@main.command(name="prompt", help="tally an item")
@model_with_completion
def _prompt(model: str) -> None:
    """
    Prompt for every field in the given model
    """
    from .autotui_ext import prompt

    prompt(_model_from_string(model))


@main.command(name="prompt-now", help="tally an item (now)")
@model_with_completion
def _prompt_now(model: str) -> None:
    """
    Prompt for every field in the model, except datetime, which should default to now
    """
    from .autotui_ext import prompt_now

    prompt_now(_model_from_string(model))


@main.command(name="recent", short_help="print recently tallied items")
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
    from .recent import query_print

    attrs = [a.strip() for a in remove_attrs.split(",") if a.strip()]
    query_print(_model_from_string(model), count, remove_attrs=attrs)


@main.command(short_help="export all data from a model")
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
    from autotui.fileio import namedtuple_sequence_dumps
    from .autotui_ext import glob_namedtuple

    itr = json.loads(
        namedtuple_sequence_dumps(list(glob_namedtuple(_model_from_string(model))))
    )

    if stream:
        for blob in itr:
            sys.stdout.write(json.dumps(blob))
            sys.stdout.write("\n")
    else:
        sys.stdout.write(json.dumps(list(itr)))
        sys.stdout.write("\n")
    sys.stdout.flush()


@main.command(short_help="merge all data for a model into one file")
@model_with_completion
@click.option("--sort-key", default=None, help="Sort resulting merged data by JSON key")
def merge(model: str, sort_key: Optional[str]) -> None:
    """
    Merge all datafiles for one model into a single '-merged.json' file
    """
    from pathlib import Path
    from datetime import datetime

    from autotui.fileio import namedtuple_sequence_dumps
    from .autotui_ext import glob_namedtuple
    from .file import glob_datafiles, ttally_temp_dir, ttally_merged_path

    datafiles: List[Path] = list(glob_datafiles(model))
    if len(datafiles) == 0:
        click.echo(f"No datafiles for model {model}", err=True)
        return

    data = json.loads(
        namedtuple_sequence_dumps(list(glob_namedtuple(_model_from_string(model))))
    )

    # if provided, use sort key
    if sort_key is not None and len(data) > 0:
        assert sort_key in data[0], f"Could not find {sort_key} in {data[0]}"
        data = list(sorted(data, key=lambda obj: obj[sort_key]))  # type: ignore[no-any-return]

    epoch = int(datetime.now().timestamp())
    cachefile = ttally_temp_dir() / f"{model}-{epoch}-merged.json"

    click.echo(f"Writing backup to '{cachefile}'", err=True)
    with cachefile.open("w") as backup_f:
        json.dump(data, backup_f)

    # remove current datafiles
    for rmf in datafiles:
        click.echo(f"Removing '{rmf}'", err=True)
        rmf.unlink()

    merge_target = ttally_merged_path(model)
    with merge_target.open("w") as merged_f:
        json.dump(data, merged_f)

    click.echo(f"Wrote merged file to '{merge_target}'", err=True)


@main.command(short_help="edit the datafile")
@model_with_completion
def edit(model: str) -> None:
    """
    Edit the current datafile with your editor
    """
    from .file import datafile as df

    _model_from_string(model)
    f = df(model.lower())
    if not f.exists():
        click.secho(f"Warning: {f} doesn't exist", err=True, fg="red")
    click.edit(filename=str(f))


if __name__ == "__main__":
    main(prog_name="ttally")
