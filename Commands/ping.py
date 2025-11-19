import socket
import time


def run(args):
    host = args[0] if args else "8.8.8.8"
    port = 80
    attempts = 4
    print(f"pinging {host} ({attempts} attempts)")
    for idx in range(1, attempts + 1):
        start = time.perf_counter()
        try:
            with socket.create_connection((host, port), timeout=2):
                pass
            elapsed = (time.perf_counter() - start) * 1000
            print(f"reply {idx}: {elapsed:.2f} ms")
        except OSError as exc:
            print(f"reply {idx}: failed ({exc})")
        time.sleep(0.5)
