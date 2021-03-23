import sys
from typing import Any

import click

from .autotui_ext import prompt, prompt_now
from .recent import query_print
from .codegen import generate_shell_aliases
from .json_stdin import save_from_stdin
from .models import MODELS


def _model_from_string(model_name: str) -> Any:
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

    prompt using default autotui behavior, writing to the tupletally datafile,
    same as above, but if the model has a datetime, set it to now,
    query the 10 most recent items for a model
    """
    pass


@main.command()
def generate() -> None:
    """
    Generate the aliases!
    """
    for a in generate_shell_aliases():
        print(a)


@main.command()
@click.argument("MODEL")
def from_json(model: str) -> None:
    """
    A way to allow external programs to save JSON data to the current file for the model
Provide a list of JSON from STDIN, and the corresponding model to parse it to
    (in lowercase) as the first argument, and this parses (validates)
    and saves it to the file
    """
    save_from_stdin(_model_from_string(model))

@main.command(name="prompt")
@click.argument("MODEL")
def _prompt(model: str) -> None:
    """
    Prompt for every field in the given model
    """
    prompt(_model_from_string(model))


@main.command(name="prompt-now")
@click.argument("MODEL")
def _prompt_now(model: str) -> None:
    """
    Prompt for every field in the model, except datetime, which should default to now
    """
    prompt_now(_model_from_string(model))


@main.command(name="recent")
@click.argument("MODEL")
@click.argument("COUNT", type=int, default=10)
def _recent(model: str, count: int) -> None:
    """
    List recent items logged for this model
    """
    query_print(_model_from_string(model), count)


if __name__ == "__main__":
    main(prog_name="tupletally")
