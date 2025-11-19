import os


def run(args):
    target = args[0] if args else os.getcwd()
    target_path = os.path.abspath(target)
    if not os.path.exists(target_path):
        print(f"ls: cannot access '{target}': No such file or directory")
        return
    if os.path.isfile(target_path):
        print(os.path.basename(target_path))
        return
    try:
        entries = sorted(os.listdir(target_path))
        for entry in entries:
            print(entry)
    except PermissionError:
        print(f"ls: cannot open directory '{target}': Permission denied")
    except Exception as exc:
        print(f"ls: {exc}")
