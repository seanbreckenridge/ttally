# tupletally

Interactive module using [`autotui`](https://github.com/seanbreckenridge/autotui) to generate code/aliases to save things I do often. Used as part of [`HPI`](https://github.com/seanbreckenridge/HPI)

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
  generate  Generate the aliases!
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
    calories: float
```

to...

```
alias food='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"food\"];t.p(m)"'
alias food-now='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"food\"];t.pn(m)"'
alias food-recent='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"food\"];t.qr(m)"'
alias shower='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"shower\"];t.p(m)"'
alias shower-now='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"shower\"];t.pn(m)"'
alias shower-recent='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"shower\"];t.qr(m)"'
alias water='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"water\"];t.p(m)"'
alias water-now='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"water\"];t.pn(m)"'
alias water-recent='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"water\"];t.qr(m)"'
alias weight='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"weight\"];t.p(m)"'
alias weight-now='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"weight\"];t.pn(m)"'
alias weight-recent='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"weight\"];t.qr(m)"'
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
