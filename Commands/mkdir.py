from pathlib import Path


def run(args):
    if not args:
        print("mkdir: missing directory name")
        return
    for target in args:
        path = Path(target).expanduser()
        try:
            path.mkdir(parents=True, exist_ok=False)
            print(f"created {path}")
        except FileExistsError:
            print(f"mkdir: {path} already exists")
        except OSError as exc:
            print(f"mkdir: cannot create {path}: {exc}")
