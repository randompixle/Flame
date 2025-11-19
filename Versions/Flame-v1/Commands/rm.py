import os, shutil
from pathlib import Path

PROTECTED = ["/","/home","/usr","/bin","/lib","/lib64","/etc","/dev","/proc","/sys","/boot","/sbin"]

def safe(p):
    p=str(Path(p).resolve())
    for prot in PROTECTED:
        if p==prot or p.startswith(prot+"/"): return True
    return False

def run(args):
    if not args:
        print("Usage: rm <target>")
        return
    p = Path(args[0]).resolve()
    if safe(p):
        print(f"rm: refusing to delete protected path: {p}")
        return
    if not p.exists():
        print(f"rm: cannot remove '{p}': No such file")
        return
    try:
        if p.is_dir(): shutil.rmtree(p)
        else: p.unlink()
        print(f"removed: {p}")
    except Exception as e:
        print(f"rm error: {e}")
