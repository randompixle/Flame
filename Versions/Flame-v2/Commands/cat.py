import os


def run(args):
    if not args:
        print("Usage: cat <file> [file...]")
        return
    for path in args:
        file_path = os.path.abspath(path)
        if not os.path.isfile(file_path):
            print(f"cat: {path}: No such file")
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as handle:
                print(handle.read(), end="")
        except Exception as exc:
            print(f"cat: {exc}")
