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

In other words, it converts this (the config file at `~/.config/tupletally.py`)

```python
from datetime import datetime
from typing import NamedTuple

# if you define a datetime on a model, the attribute name should be 'when'


class Shower(NamedTuple):
    when: datetime


class Weight(NamedTuple):
    when: datetime
    pounds: float


class Water(NamedTuple):
    when: datetime
    glasses: float

```

to...

```
alias shower='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"shower\"];t.prompt(m)"'
alias shower-now='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"shower\"];t.prompt_now(m)"'
alias shower-recent='python3 -c "import tupletally.codegen as t;t.query_print(\"shower\")"'
alias water='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"water\"];t.prompt(m)"'
alias water-now='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"water\"];t.prompt_now(m)"'
alias water-recent='python3 -c "import tupletally.codegen as t;t.query_print(\"water\")"'
alias weight='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"weight\"];t.prompt(m)"'
alias weight-now='python3 -c "import tupletally.codegen as t;m=t.MODELS[\"weight\"];t.prompt_now(m)"'
alias weight-recent='python3 -c "import tupletally.codegen as t;t.query_print(\"weight\")"'
```

Whenever I run any of those aliases, it opens an interactive interface like this:

<img src="https://raw.githubusercontent.com/seanbreckenridge/autotui/master/.assets/builtin_demo.gif">

... which saves that information to a JSON file:

```json
[
  {
    "when": 1598856786,
    "glass_count": 2.0
  }
]
```

This also gives me `{tuple}-recent` aliases, which print the 10 most recent items I've logged. For example:

```python
> water-recent
Water(when=datetime.datetime(2021, 3, 19, 20, 20, 27, tzinfo=datetime.timezone.utc), glasses=1.0)
Water(when=datetime.datetime(2021, 3, 19, 14, 33, 57, tzinfo=datetime.timezone.utc), glasses=1.0)
Water(when=datetime.datetime(2021, 3, 19, 9, 41, 53, tzinfo=datetime.timezone.utc), glasses=1.0)
Water(when=datetime.datetime(2021, 3, 19, 8, 28, 10, tzinfo=datetime.timezone.utc), glasses=1.0)
Water(when=datetime.datetime(2021, 3, 19, 7, 14, 34, tzinfo=datetime.timezone.utc), glasses=1.5)
Water(when=datetime.datetime(2021, 3, 19, 3, 39, 56, tzinfo=datetime.timezone.utc), glasses=0.75)
Water(when=datetime.datetime(2021, 3, 19, 0, 16, 42, tzinfo=datetime.timezone.utc), glasses=1.0)
Water(when=datetime.datetime(2021, 3, 18, 5, 5, 19, tzinfo=datetime.timezone.utc), glasses=1.0)
Water(when=datetime.datetime(2021, 3, 18, 3, 17, 26, tzinfo=datetime.timezone.utc), glasses=1.5)
Water(when=datetime.datetime(2021, 3, 18, 3, 5, 14, tzinfo=datetime.timezone.utc), glasses=1.0)
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

```shell
git clone https://github.com/seanbreckenridge/tupletally
cd ./tupletally
pip install .
# setup a ~/.config/tupletally.py file.
# You can use the block above as a starting point,
# or start off with mine:
curl -s "https://sean.fish/d/tupletally.py" > ~/.config/tupletally.py
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
