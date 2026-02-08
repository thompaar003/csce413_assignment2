#!/usr/bin/env python3
"""
Port Scanner - Starter Template for Students
Assignment 2: Network Security

This is a STARTER TEMPLATE to help you get started.
You should expand and improve upon this basic implementation.

TODO for students:
1. Implement multi-threading for faster scans
2. Add banner grabbing to detect services
3. Add support for CIDR notation (e.g., 192.168.1.0/24)
4. Add different scan types (SYN scan, UDP scan, etc.)
5. Add output formatting (JSON, CSV, etc.)
6. Implement timeout and error handling
7. Add progress indicators
8. Add service fingerprinting
"""

import socket
import sys
import concurrent.futures
import argparse
from tqdm import tqdm


def scan_port(target, port, timeout=1.0):
    """
    Scan a single port on the target host

    Args:
        target (str): IP address or hostname to scan
        port (int): Port number to scan
        timeout (float): Connection timeout in seconds

    Returns:
        bool: True if port is open, False otherwise
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create socket
        s.settimeout(1.0)
        result = s.connect_ex((target,port)) # Returns 0 if successful

        banner = "None"
        if result == 0:
            try:
                banner = s.recv(1024).decode().strip()
            except:
                banner = "No Banner Received"

        s.close()

        return not result, banner

    except (socket.timeout, ConnectionRefusedError, OSError):
        return False, None


def scan_range(target, start_port, end_port, threads):
    """
    Scan a range of ports on the target host

    Args:
        target (str): IP address or hostname to scan
        start_port (int): Starting port number
        end_port (int): Ending port number

    Returns:
        list: List of open ports
    """
    open_ports = []
    ports = range(start_port, end_port + 1)

    print(f"[*] Scanning {target} from port {start_port} to {end_port} using {threads} workers.")
    print(f"[*] This may take a while...")
    with tqdm(total=len(ports), desc=f"Scanning {target}", unit="port") as progbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as worker:
            
            # Assigns jobs to each worker
            future_to_port = {worker.submit(scan_port, target, port): port for port in ports}

            for future in concurrent.futures.as_completed(future_to_port):
                progbar.update(1)
                port = future_to_port[future]
                try:
                    is_open, banner = future.result()
                    if is_open:
                        tqdm.write(f"[!] Port {port}: open")
                        open_ports.append((port, banner))
                except Exception:
                    pass # Worker found closed port

    return sorted(open_ports, key=lambda x: x[0])


def main():
    """Main function"""

    #python3 main.py --target 172.20.0.0/24 --ports 1-1000 --threads 16

    parser = argparse.ArgumentParser(description="Port Scanner")
    parser.add_argument("--target", required=True, help="Target IP or hostname")
    parser.add_argument("--ports", default="1-1024", help="Port range (e.g., 1-1000)")
    parser.add_argument("--threads", type=int, default=100, help="Number of workers")

    args = parser.parse_args()

    workers = args.threads
    target = args.target
    ports_arg = args.ports
    if "-" in ports_arg:
        parts = ports_arg.split("-")

        start_port = int(parts[0])
        end_port = int(parts[1])
    else:
        # Handle the case where the user only provides a single port
        start_port = end_port = int(ports_arg)

    print(f"[*] Starting port scan on {target} using {workers} workers")

    open_ports = scan_range(target, start_port, end_port, workers)

    print(f"\n[+] Scan complete!")
    print(f"{'PORT':<10} {'STATE':<10} {'SERVICE/BANNER'}")
    print("-" * 50)
    print(f"[+] Found {len(open_ports)} open ports:")
    for port, banner in open_ports:
        service_info = banner if banner else "Unknown Service"
        print(f"{port:<10} {'open':<10} {service_info}")

if __name__ == "__main__":
    main()
