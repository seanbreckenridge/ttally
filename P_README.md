# ttally

Interactive module using [`autotui`](https://github.com/seanbreckenridge/autotui) to save things I do often to JSON. Used as part of [`HPI`](https://github.com/seanbreckenridge/HPI)

Given a `NamedTuple` defined in [`~/.config/ttally.py`](https://sean.fish/d/ttally.py), this creates interactive interfaces which validate my input to log information to JSON files

Currently, I use this to store info like whenever I drink water/shower/my current weight periodically

```
>>>PMARK
perl -E 'print "`"x3, "\n"'
ttally --help
perl -E 'print "`"x3, "\n"'
```

In other words, it converts this (the config file at `~/.config/ttally.py`):

```
>>>PMARK
perl -E 'print "`"x3, "python", "\n"'
cat ~/.config/ttally.py
perl -E 'print "`"x3, "\n"'
```

to...

```
>>>PMARK
perl -E 'print "`"x3, "\n"'
ttally generate
perl -E 'print "`"x3, "\n"'
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

The whole point of this interface is that it validates my input to types, stores it as a basic editable format (JSON), but is still loadable into typed ADT-like Python objects, with minimal boilerplate. I just need to add a NamedTuple to `~/.config/ttally.py`, and all the interfaces and resulting JSON files are generated.

To load the items into python, you can do:

```python
from ttally.autotui_ext import glob_namedtuple
from ttally.config import Water

print(list(glob_namedtuple(Water)))
```

See [`here`](https://github.com/seanbreckenridge/HPI/blob/master/my/body.py) for my usage in `HPI`.

## Installation

```bash
pip install 'git+https://github.com/seanbreckenridge/ttally'
```

### Configuration

You need to setup a `~/.config/ttally.py` file. You can use the block above as a starting point, or with mine:

```bash
curl -s 'https://sean.fish/d/ttally.py' > ~/.config/ttally.py
```

You can set the `TTALLY_DATA_DIR` environment variable to the directory that `ttally` should save data to, defaults to `~/.local/share/ttally`. If you want to use a different path for configuration, you can set the `TTALLY_CFG` to the absolute path to the file.

I cache the generated aliases by putting a block like this in my shell config (i.e. it runs the first time I start a terminal, but then stays the same until I remove the file/my computer restarts):

```bash
TTALLY_ALIASES="${HOME}/.cache/ttally_aliases"
if [[ ! -e "${TTALLY_ALIASES}" ]]; then
	if havecmd ttally; then
		python3 -m ttally generate >"${TTALLY_ALIASES}"
	fi
fi
[[ -e "${TTALLY_ALIASES}" ]] && source "${TTALLY_ALIASES}"
```
