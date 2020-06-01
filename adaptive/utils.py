import sys
from pathlib import Path

import pandas as pd

days  = 1
weeks = 7 


def root_from_cmd_args(default: str = ".") -> Path:
    if len(sys.argv) > 2 and sys.argv[1] == "--root":
        return Path(sys.argv[2])
    return Path(default).resolve()

def cwd() -> Path:
    argv0 = sys.argv[0]
    if argv0.endswith("ipython"):
        return Path(".").resolve()
    return Path(argv0).resolve().parent
        
def fmt_params(**kwargs) -> str:
    return ", ".join(f"{k.replace('_', ' ')}: {v}" for (k, v) in kwargs.items())

def assume_missing_0(df: pd.DataFrame, col: str):
    return df[col] if col in df.columns else 0
