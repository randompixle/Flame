import os


def run(args):
    if not args:
        print("Usage: mkdir <directory> [directory...]")
        return
    for path in args:
        expanded = os.path.abspath(path)
        try:
            os.makedirs(expanded, exist_ok=False)
            print(f"Created directory: {expanded}")
        except FileExistsError:
            print(f"mkdir: cannot create directory '{path}': File exists")
        except Exception as exc:
            print(f"mkdir: {exc}")
