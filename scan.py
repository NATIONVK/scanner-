"""Authorized-use TCP port checker. Keep this utility separate from the research lab."""
import argparse
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime


def check_port(host, port, timeout=0.5):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return port if sock.connect_ex((host, port)) == 0 else None
    except OSError:
        return None


def main():
    parser = argparse.ArgumentParser(description="Check TCP ports on a system you are authorized to test.")
    parser.add_argument("host", help="IP address or hostname")
    parser.add_argument("--start", type=int, default=1, help="First port (default: 1)")
    parser.add_argument("--end", type=int, default=1000, help="Last port (default: 1000)")
    parser.add_argument("--workers", type=int, default=100, help="Concurrent workers (1-200)")
    parser.add_argument("--timeout", type=float, default=0.5, help="Socket timeout in seconds")
    args = parser.parse_args()

    if not (1 <= args.start <= args.end <= 65535):
        parser.error("ports must satisfy 1 <= start <= end <= 65535")
    if not (1 <= args.workers <= 200):
        parser.error("--workers must be between 1 and 200")
    if not (0.1 <= args.timeout <= 5):
        parser.error("--timeout must be between 0.1 and 5 seconds")

    print("AUTHORIZED TESTING ONLY — scan only systems you own or have permission to assess.")
    try:
        resolved = socket.gethostbyname(args.host)
    except socket.gaierror:
        parser.error("Could not resolve the supplied host.")

    print("-" * 64)
    print(f"Target: {args.host} ({resolved})")
    print(f"Started: {datetime.now().isoformat(timespec='seconds')}")
    print(f"Ports: {args.start}-{args.end} | Workers: {args.workers}")
    print("-" * 64)

    started = datetime.now()
    open_ports = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(check_port, resolved, port, args.timeout)
                   for port in range(args.start, args.end + 1)]
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                open_ports.append(result)
                print(f"[OPEN] TCP/{result}")

    print("-" * 64)
    print(f"Completed in {datetime.now() - started}")
    print("Open ports:", ", ".join(map(str, sorted(open_ports))) if open_ports else "None detected")


if __name__ == "__main__":
    main()
