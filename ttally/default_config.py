import os
from pathlib import Path

URL = "https://github.com/seanbreckenridge/ttally"


def default_config_file() -> Path:
    cfg_file: str = os.environ.get("TTALLY_CFG", "~/.config/ttally.py")
    cfg_path = Path(cfg_file).expanduser().absolute()
    if not cfg_path.exists():
        raise FileNotFoundError(
            f"Expected configuration to exist at {cfg_path}, see {URL} for an example"
        )
    return cfg_path


ttally_config_path = str(default_config_file())
