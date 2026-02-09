#!/usr/bin/env python3
"""Starter template for the port knocking client."""

import argparse
import socket
import time
import subprocess

DEFAULT_KNOCK_SEQUENCE = [1234, 5678, 9012]
DEFAULT_PROTECTED_PORT = 2222
DEFAULT_DELAY = 0.3


def send_knock(target, port, delay):
    """Send a single knock to the target port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(1.0)

            sock.sendto(b'Knock', (target, port))

            print(f"Sent UDP knock to {target}:{port}")
    except OSError:
        print(f"Error knocking on {port}: {e}")
    time.sleep(delay)


def perform_knock_sequence(target, sequence, delay):
    """Send the full knock sequence."""
    for port in sequence:
        send_knock(target, port, delay)


def check_protected_port(target, protected_port):
    """Try connecting to the protected port after knocking."""
    command = [
        "ssh",
        "-v",                 
        "-p", str(protected_port),
        "-o", "ConnectTimeout=3",
        "-o", "BatchMode=yes", 
        "-o", "StrictHostKeyChecking=no",
        f"sshuser@{target}",
        "exit"
    ]
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True
        )
        
        if "Connection established" in result.stderr:
             print(f"[SUCCESS] The Firewall is OPEN! (SSH Handshake completed)")
        else:
             print(f"[-] Connection timed out or refused.")
    except OSError:
        print(f"[-] Could not connect to protected port {protected_port}")


def parse_args():
    parser = argparse.ArgumentParser(description="Port knocking client starter")
    parser.add_argument("--target", required=True, help="Target host or IP")
    parser.add_argument(
        "--sequence",
        default=",".join(str(port) for port in DEFAULT_KNOCK_SEQUENCE),
        help="Comma-separated knock ports",
    )
    parser.add_argument(
        "--protected-port",
        type=int,
        default=DEFAULT_PROTECTED_PORT,
        help="Protected service port",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DEFAULT_DELAY,
        help="Delay between knocks in seconds",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Attempt connection to protected port after knocking",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        sequence = [int(port) for port in args.sequence.split(",")]
    except ValueError:
        raise SystemExit("Invalid sequence. Use comma-separated integers.")

    perform_knock_sequence(args.target, sequence, args.delay)

    if args.check:
        check_protected_port(args.target, args.protected_port)


if __name__ == "__main__":
    main()
