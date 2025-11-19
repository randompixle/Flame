import shutil
from pathlib import Path


def run(args):
    if not args:
        print("rm: missing target")
        return
    for target in args:
        path = Path(target).expanduser()
        if not path.exists():
            print(f"rm: {path} not found")
            continue
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            print(f"removed {path}")
        except OSError as exc:
            print(f"rm: failed to remove {path}: {exc}")
