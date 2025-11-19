from pathlib import Path

def run(args):
    if not args:
        print("Usage: cat <file>")
        return
    p=Path(args[0])
    if not p.exists():
        print(f"cat: {p}: No such file")
        return
    if p.is_dir():
        print(f"cat: {p}: Is a directory")
        return
    print(p.read_text(errors="ignore"))
