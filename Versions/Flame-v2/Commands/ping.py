import time


def run(args):
    target = args[0] if args else "flame"
    delay = 0.05
    for _ in range(3):
        print(f"Pinging {target}...")
        time.sleep(delay)
    print(f"Reply from {target}: flame is alive")
