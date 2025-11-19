import os
import shutil


def _remove_path(path: str) -> None:
    if os.path.isdir(path) and not os.path.islink(path):
        shutil.rmtree(path)
    else:
        os.remove(path)


def run(args):
    if not args:
        print("Usage: rm <path> [path...]")
        return
    for target in args:
        expanded = os.path.abspath(target)
        if not os.path.exists(expanded):
            print(f"rm: cannot remove '{target}': No such file or directory")
            continue
        try:
            _remove_path(expanded)
            print(f"Removed: {expanded}")
        except Exception as exc:
            print(f"rm: {exc}")
