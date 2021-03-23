# tupletally

Interactive module using [`autotui`](https://github.com/seanbreckenridge/autotui) to save things I do often to JSON. Used as part of [`HPI`](https://github.com/seanbreckenridge/HPI)

Given a `NamedTuple` (hence the name) defined in [`~/.config/tupletally.py`](https://sean.fish/d/tupletally.py), this creates interactive interfaces which validate my input to log information to JSON files

Currently, I use this to store info like whenever I drink water/shower/my current weight periodically

```
Usage: tupletally [OPTIONS] COMMAND [ARGS]...

  Tally things that I do often!

  Given a few namedtuples, this creates serializers/deserializers and an
  interactive interface using 'autotui', and aliases to:

  prompt using default autotui behavior, writing to the tupletally datafile,
  same as above, but if the model has a datetime, set it to now, query the
  10 most recent items for a model

Options:
  --help  Show this message and exit.

Commands:
  from-json   A way to allow external programs to save JSON data to the...
  generate    Generate the aliases!
  prompt      Prompt for every field in the given model
  prompt-now  Prompt for every field in the model, except datetime, which...
  recent      List recent items logged for this model
```

In other words, it converts this (the config file at `~/.config/tupletally.py`):

```python
from datetime import datetime
from typing import NamedTuple


class Shower(NamedTuple):
    when: datetime


class Weight(NamedTuple):
    when: datetime
    pounds: float


class Water(NamedTuple):
    when: datetime
    glasses: float


class Food(NamedTuple):
    when: datetime
    food: str
    calories: int
```

to...

```
alias food='python3 -m tupletally prompt food'
alias food-now='python3 -m tupletally prompt-now food'
alias food-recent='python3 -m tupletally recent food'
alias shower='python3 -m tupletally prompt shower'
alias shower-now='python3 -m tupletally prompt-now shower'
alias shower-recent='python3 -m tupletally recent shower'
alias water='python3 -m tupletally prompt water'
alias water-now='python3 -m tupletally prompt-now water'
alias water-recent='python3 -m tupletally recent water'
alias weight='python3 -m tupletally prompt weight'
alias weight-now='python3 -m tupletally prompt-now weight'
alias weight-recent='python3 -m tupletally recent weight'
```

Whenever I run any of those aliases, it opens an interactive interface like this:

<img src="https://raw.githubusercontent.com/seanbreckenridge/autotui/master/.assets/builtin_demo.gif">

... which saves that information to a JSON file:

```json
[
  {
    "when": 1598856786,
    "glasses": 2.0
  }
]
```

The `{tuple}-now` aliases set the any `datetime` values for the prompted tuple to now

This also gives me `{tuple}-recent` aliases, which print the 10 most recent items I've logged. For example:

```
$ water-recent 5
2021-03-20 18:23:24     2.0
2021-03-20 01:28:27     1.0
2021-03-19 23:34:12     1.0
2021-03-19 22:49:05     1.5
2021-03-19 16:05:34     1.0
```

The `from-json` command can be used to send this JSON which matches a model, i.e. providing a non-interactive interface, incase I want to [call this from a script](https://github.com/seanbreckenridge/HPI/blob/master/scripts/food-fzf)

## Library Usage

The whole point of this interface is that it validates my input to types, stores it as a basic editable format (JSON), but is still loadable into typed ADT-like Python objects, with minimal boilerplate. I just need to add a NamedTuple to `~/.config/tupletally.py`, and all the interfaces and resulting JSON files are generated.

To load the items into python, you can do:

```python
from tupletally.autotui_ext import glob_namedtuple
from tupletally.config import Water

print(list(glob_namedtuple(Water)))
```

See [`here`](https://github.com/seanbreckenridge/HPI/blob/master/my/body.py) for my usage in `HPI`.

## Installation

```bash
pip install 'git+https://github.com/seanbreckenridge/tupletally'
```

### Configuration

You need to setup a `~/.config/tupletally.py` file. You can use the block above as a starting point, or with mine:

```bash
curl -s 'https://sean.fish/d/tupletally.py' > ~/.config/tupletally.py
```

You can set the `TUPLETALLY_DATA_DIR` environment variable to the directory that `tupletally` should save data to, defaults to `~/.local/share/tupletally`. If you want to use a different path for configuration, you can set the `TUPLETALLY_CFG` to the absolute path to the file.

I cache the generated aliases by putting a block like this in my shell config (i.e. it runs the first time I start a terminal, but then stays the same until I remove the file/my computer restarts):

```bash
TUPLETALLY_ALIASES='/tmp/tupletally_aliases'
if [[ ! -e "${TUPLETALLY_ALIASES}" ]]; then
  python3 -m tupletally generate >"${TUPLETALLY_ALIASES}"
fi
source "${TUPLETALLY_ALIASES}"
```
