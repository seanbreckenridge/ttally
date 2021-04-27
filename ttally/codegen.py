from typing import Iterator

from .models import MODELS


def generate_shell_aliases(python_loc: str = "python3") -> Iterator[str]:
    pre = f"'{python_loc} -m ttally "
    suf = "'"
    for mname, model in MODELS.items():
        yield f"alias {mname}={pre}prompt {mname}{suf}"
        yield f"alias {mname}-now={pre}prompt-now {mname}{suf}"
        yield f"alias {mname}-recent={pre}recent {mname}{suf}"
