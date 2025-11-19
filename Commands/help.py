from builtins import FLAME_CONTEXT


def run(args):
    commands = FLAME_CONTEXT.list_commands()
    if not commands:
        print("no commands loaded")
        return
    print("available commands:")
    for name in commands:
        print(f"  - {name}")
