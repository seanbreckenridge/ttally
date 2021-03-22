from typing import Iterator, Any

from .autotui_ext import prompt, prompt_now
from .models import MODELS
from .recent import query_print


def generate_shell_aliases(python_loc: str = "python3") -> Iterator[str]:
    pre = f"'{python_loc} -c \"import tupletally.codegen as t;"
    suf = "\"'"
    for mname, model in MODELS.items():
        quoted_mname = f'\\"{mname}\\"'
        set_model = f"m=t.MODELS[{quoted_mname}];"
        yield f"alias {mname}={pre}{set_model}t.p(m){suf}"
        yield f"alias {mname}-now={pre}{set_model}t.pn(m){suf}"
        yield f"alias {mname}-recent={pre}t.qr({quoted_mname}){suf}"


# shorthands for aliases
# and so that imports are used in the file


def p(nt: Any) -> None:
    prompt(nt)


def pn(nt: Any) -> None:
    prompt_now(nt)


def qr(ns: str) -> None:
    query_print(ns)
