from pathlib import Path


def run(args):
    target = Path(args[0]).expanduser() if args else Path.cwd()
    if not target.exists():
        print(f"ls: {target} not found")
        return
    if target.is_file():
        print(target.name)
        return
    try:
        entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    except OSError as exc:
        print(f"ls: cannot access {target}: {exc}")
        return
    for entry in entries:
        suffix = "/" if entry.is_dir() else ""
        print(entry.name + suffix)
