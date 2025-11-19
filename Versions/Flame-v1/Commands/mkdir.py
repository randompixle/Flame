import os
from pathlib import Path

def run(args):
    if not args:
        print("Usage: mkdir <directory>")
        return
    p = Path(args[0])
    try:
        p.mkdir(parents=True,exist_ok=False)
        print(f"directory created: {p}")
    except Exception as e:
        print(f"mkdir error: {e}")
