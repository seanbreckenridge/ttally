from typing import Iterator

from .autotui_ext import namedtuple_func_name, prompt, prompt_now
from .models import MODELS
from .recent import query_print


def generate_shell_aliases(python_loc: str = "python3") -> Iterator[str]:
    pre = f"'{python_loc} -c \"import tupletally.codegen as t;"
    suf = "\"'"
    for mname, model in MODELS.items():
        quoted_mname = f'\\"{mname}\\"'
        set_model = f"m=t.MODELS[{quoted_mname}];"
        yield f"alias {mname}={pre}{set_model}t.prompt(m){suf}"
        yield f"alias {mname}-now={pre}{set_model}t.prompt_now(m){suf}"
        yield f"alias {mname}-recent={pre}t.query_print({quoted_mname}){suf}"
