import click

from .codegen import generate_shell_aliases


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


if __name__ == "__main__":
    main(prog_name="tupletally")
