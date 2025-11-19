import os
from pathlib import Path
BLUE="\033[34m"; YELLOW="\033[33m"; GREEN="\033[32m"; RESET="\033[0m"

def color(i):
    p=Path(i)
    if p.is_dir(): return f"{BLUE}{i}{RESET}"
    if p.suffix==".py": return f"{YELLOW}{i}{RESET}"
    if os.access(p,os.X_OK): return f"{GREEN}{i}{RESET}"
    return i

def run(args):
    path = Path(args[0]) if args else Path.cwd()
    if not path.exists():
        print(f"ls: cannot access '{path}'")
        return
    for item in sorted(os.listdir(path)):
        print(color(item))
