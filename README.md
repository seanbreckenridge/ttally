# ttally

**TL;DR**: This converts a file like this (config file at `~/.config/ttally.py`):

```python
# This defines some models for things I want to log often
# which then generate into TUIs using:
# https://github.com/seanbreckenridge/ttally

from datetime import datetime
from typing import NamedTuple

from seanb.ttally_self import SelfTypes


class Self(NamedTuple):
    when: datetime
    what: SelfTypes


class Weight(NamedTuple):
    when: datetime
    pounds: float


# this also tracks water, either by attaching it
# to the corresponding food, or by just adding
# something with the text 'water'
class Food(NamedTuple):
    when: datetime
    calories: int
    food: str
    quantity: float
    water: int  # ml

    # if I don't supply a quantity, default to 1
    @staticmethod
    def attr_validators() -> dict:
        # https://sean.fish/d/ttally_types.py?dark
        from seanb.ttally_types import prompt_float_default

        return {"quantity": lambda: prompt_float_default("quantity")}


# e.g. a concert or something
class Event(NamedTuple):
    event_type: str
    when: datetime
    description: str
    score: int | None
    comments: str | None

    @staticmethod
    def attr_validators() -> dict:
        # https://sean.fish/d/ttally_types.py?dark
        from seanb.ttally_types import edit_in_vim

        return {"comments": edit_in_vim}
```

to (shell aliases)...

```
alias event='python3 -m ttally prompt event'
alias event-now='python3 -m ttally prompt-now event'
alias event-recent='python3 -m ttally recent event'
alias food='python3 -m ttally prompt food'
alias food-now='python3 -m ttally prompt-now food'
alias food-recent='python3 -m ttally recent food'
alias self='python3 -m ttally prompt self'
alias self-now='python3 -m ttally prompt-now self'
alias self-recent='python3 -m ttally recent self'
alias weight='python3 -m ttally prompt weight'
alias weight-now='python3 -m ttally prompt-now weight'
alias weight-recent='python3 -m ttally recent weight'
```

Whenever I run any of those aliases, it inspects the model in the config file, dynamically creates and runs an interactive interface like this:

<img src="https://raw.githubusercontent.com/seanbreckenridge/autotui/master/.assets/builtin_demo.gif">

... which saves some information I enter to a file:

```yaml
- when: 1598856786,
  glasses": 2.0
```

---

`ttally` is an interactive module using [`autotui`](https://github.com/seanbreckenridge/autotui) to save things I do often to YAML

Currently, I use this to store info like whenever I eat something/drink water/my current weight/random thoughts periodically

Given a `NamedTuple` defined in [`~/.config/ttally.py`](https://sean.fish/d/ttally.py?dark), this creates interactive interfaces which validate my input to save information to JSON/YAML files

The `{tuple}-now` aliases set the any `datetime` values for the prompted tuple to now

This also gives me `{tuple}-recent` aliases, which print recent items I've logged. For example:

```
$ water-recent 5
2021-03-20 18:23:24     2.0
2021-03-20 01:28:27     1.0
2021-03-19 23:34:12     1.0
2021-03-19 22:49:05     1.5
2021-03-19 16:05:34     1.0
```

## Library Usage

The whole point of this interface is that it validates my input to types, stores it as a basic editable format (YAML), but is still loadable into typed python objects, with minimal boilerplate. I just need to add a NamedTuple to `~/.config/ttally.py`, and all the interactive interfaces and resulting YAML files are automatically created

This intentionally uses YAML and doesn't store the info into a single "merged" database. A single database:

- requires some way to edit/delete items - at that point I'm essentially re-implementing a CRUD interface _again_
- makes it harder to merge them together ([I've tried](https://github.com/seanbreckenridge/calories-scripts/blob/master/calmerge))

YAML isn't perfect but at least I can open it in vim and delete/edit some value. Since the YAML files are pretty-printed, its also pretty trivial to grep/duplicate items by copying a few lines around. Without writing a bunch of code, this seems like the least amount of friction to immediately create new interfaces

The YAML files are versioned with the date/OS/platform, so I'm able to add items on my linux, mac, or android (using [`termux`](https://termux.com/)) and sync them across all my devices using [`SyncThing`](https://syncthing.net/). Those look like:

```
food-darwin-seans-mbp.localdomain-2021-03.yaml
food-linux-bastion-2021-03.yaml
food-linux-localhost-2021-04.yaml
```

... which can then be combined back into python, like:

```python
from more_itertools import take  # just to grab a few items

from ttally.autotui_ext import glob_namedtuple
from ttally.config import Food

> take(3, glob_namedtuple(Food))

[Food(when=datetime.datetime(2020, 9, 27, 6, 49, 34, tzinfo=datetime.timezone.utc), calories=440, food='ramen, egg'),
Food(when=datetime.datetime(2020, 9, 27, 6, 52, 16, tzinfo=datetime.timezone.utc), calories=160, food='2 eggs'),
Food(when=datetime.datetime(2020, 9, 27, 6, 53, 44, tzinfo=datetime.timezone.utc), calories=50, food='ginger chai')]
```

The `from-json` command can be used to send this JSON which matches a model, i.e. providing a non-interactive interface to add items, in case I want to [call this from a script](bin/cz)

`hpi query` from [`HPI`](https://github.com/seanbreckenridge/HPI) can be used with the `ttally.funcs` module, like:

```bash
# how many calories in the last day
$ hpi query ttally.funcs.food --recent 1d -s | jq -r '(.quantity)*(.calories)' | datamash sum 1
2252
```

If you'd prefer to use JSON files, you can set the `TTALLY_EXT=json` environment variable.

This can still load data from YAML or JSON (or both), every couple months I'll combine all the versioned files to a single merged file using the `export` command:

```
ttally export food > food_merged.json
```

## Installation

```bash
pip install 'git+https://github.com/seanbreckenridge/ttally'
```

```
Usage: ttally [OPTIONS] COMMAND [ARGS]...

  Tally things that I do often!

  Given a few namedtuples, this creates serializers/deserializers and an
  interactive interface using 'autotui', and aliases to:

  prompt using default autotui behavior, writing to the ttally datafile, same
  as above, but if the model has a datetime, set it to now, query the 10 most
  recent items for a model

Options:
  --help  Show this message and exit.

Commands:
  datafile    print the datafile location
  edit        edit the datafile
  export      export all data from a model
  from-json   add item by piping JSON
  generate    generate shell aliases
  merge       merge all data for a model into one file
  models      list models
  prompt      tally an item
  prompt-now  tally an item (now)
  recent      print recently tallied items
```

### Configuration

You need to setup a `~/.config/ttally.py` file. You can use the block above as a starting point, or with mine:

```bash
curl -s 'https://sean.fish/d/ttally.py' > ~/.config/ttally.py
```

You can set the `TTALLY_DATA_DIR` environment variable to the directory that `ttally` should save data to, defaults to `~/.local/share/ttally`. If you want to use a different path for configuration, you can set the `TTALLY_CFG` to the absolute path to the file.

I cache the generated aliases by putting a block like this in my shell config (i.e., it runs the first time I start a terminal, but then stays the same until I remove the file):

```bash
TTALLY_ALIASES="${HOME}/.cache/ttally_aliases"
if [[ ! -e "${TTALLY_ALIASES}" ]]; then  # alias file doesn't exist
	if havecmd ttally; then  # if ttally is installed
		python3 -m ttally generate >"${TTALLY_ALIASES}"  # generate and save the aliases
	fi
fi
[[ -e "${TTALLY_ALIASES}" ]] && source "${TTALLY_ALIASES}"  # if the file exists, make the aliases available
```

### Shell Scripts

[`cz`](bin/cz) lets me fuzzy select something I've eaten in the past using [`fzf`](https://github.com/junegunn/fzf), like:

![](https://raw.githubusercontent.com/seanbreckenridge/calories-fzf/master/demo.gif)
