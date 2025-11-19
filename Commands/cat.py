from pathlib import Path


def run(args):
    if not args:
        print("cat: missing file")
        return
    for target in args:
        path = Path(target).expanduser()
        if not path.exists():
            print(f"cat: {path} not found")
            continue
        if path.is_dir():
            print(f"cat: {path} is a directory")
            continue
        try:
            print(path.read_text())
        except OSError as exc:
            print(f"cat: cannot read {path}: {exc}")
