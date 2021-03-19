# tupletally

Note: WIP, see bottom of README for todos

Interactive module using [`autotui`](https://github.com/seanbreckenridge/autotui) to generate code/aliases to save things I do often

Given a `NamedTuple` (hence the name) defined in [`tupletally/models.py`](tupletally/models.py)

Currently, I use this to store info like whenever I drink water/shower/log my current weight periodically

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

In other words, it converts this:

```
import sys
import inspect

from datetime import datetime
from typing import NamedTuple, Any

# if you define a datetime on a model, the attribute name should be 'when'


class Shower(NamedTuple):
    when: datetime


class Weight(NamedTuple):
    when: datetime
    pounds: float


class Water(NamedTuple):
    when: datetime
    glasses: float


def _class_defined_in_module(o: Any) -> bool:
    return inspect.isclass(o) and o.__module__ == __name__


# dynamically create a list of each of these
MODELS = {
    name.casefold(): klass
    for name, klass in inspect.getmembers(
        sys.modules[__name__], _class_defined_in_module
    )
}
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

```
$ water-recent
[Water(when=datetime.datetime(2021, 3, 19, 9, 41, 53, tzinfo=datetime.timezone.utc), glasses=1.0),
 Water(when=datetime.datetime(2021, 3, 19, 8, 28, 10, tzinfo=datetime.timezone.utc), glasses=1.0),
 Water(when=datetime.datetime(2021, 3, 19, 7, 14, 34, tzinfo=datetime.timezone.utc), glasses=1.5),
 Water(when=datetime.datetime(2021, 3, 19, 3, 39, 56, tzinfo=datetime.timezone.utc), glasses=0.75),
 Water(when=datetime.datetime(2021, 3, 19, 0, 16, 42, tzinfo=datetime.timezone.utc), glasses=1.0),
 Water(when=datetime.datetime(2021, 3, 18, 5, 5, 19, tzinfo=datetime.timezone.utc), glasses=1.0),
 Water(when=datetime.datetime(2021, 3, 18, 3, 17, 26, tzinfo=datetime.timezone.utc), glasses=1.5),
 Water(when=datetime.datetime(2021, 3, 18, 3, 5, 14, tzinfo=datetime.timezone.utc), glasses=1.0),
 Water(when=datetime.datetime(2021, 3, 17, 10, 2, 56, tzinfo=datetime.timezone.utc), glasses=1.0),
 Water(when=datetime.datetime(2021, 3, 17, 4, 8, 42, tzinfo=datetime.timezone.utc), glasses=1.0)
```

## Installation

```shell
git clone https://github.com/seanbreckenridge/tupletally
cd ./tupletally
# edit tupletally/models.py to whatever models you want
pip install .
```

You can set the `TUPLETALLY_DATA_DIR` environment variable to the directory that `tupletally` should save data to, defaults to `~/data/tupletally`

I cache the generated aliases by putting a block like this in my shell config (i.e. it runs the first time I start a terminal, but then stays the same until I remove the file/my computer restarts):

```bash
TUPLETALLY='/tmp/tupletally_aliases'
if [[ ! -e "${TUPLETALLY}" ]]; then
  tupletally generate >"${TUPLETALLY}"
fi
source "${TUPLETALLY}"
```

---

Note: still finishing up the interface for this, so will probably change a bit, i.e. the following:

- change models.py to import from `~/.config/tupletally.py`? using importlib hackery?
- change default from `~/data/tupletally` to something else?
- add python library usage, for `glob_namedtuple`
- add command to combine/print model as JSON
