#!/usr/bin/env python3
"""Starter template for the port knocking server."""

import argparse
import logging
import socket
import time
import select
import subprocess
import threading

DEFAULT_KNOCK_SEQUENCE = [1234, 5678, 9012]
DEFAULT_PROTECTED_PORT = 2222
DEFAULT_SEQUENCE_WINDOW = 10.0


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def open_protected_port(ip_address, protected_port):
    """Open the protected port using firewall rules."""
    command = [
        "iptables", "-I", "INPUT",
        "-s", ip_address,
        "-p", "tcp",
        "--dport", str(protected_port),
        "-j", "ACCEPT"
    ]
    
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to open port: {e}")


def close_protected_port(ip_address, protected_port):
    """Close the protected port using firewall rules."""
    # -D (Delete) instead of -I (Insert)
    command = [
        "iptables", "-D", "INPUT",
        "-s", ip_address,
        "-p", "tcp",
        "--dport", str(protected_port),
        "-j", "ACCEPT"
    ]
    
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logging.warning(f"Failed to close port: {e}")


def listen_for_knocks(sequence, window_seconds, protected_port):
    """Listen for knock sequence and open the protected port."""
    logger = logging.getLogger("KnockServer")
    logger.info("Listening for knocks: %s", sequence)
    logger.info("Protected port: %s", protected_port)


    sockets_to_watch = []
    socket_port_map = {}
    
    for port_num in sequence:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind(('0.0.0.0', port_num))
            sockets_to_watch.append(sock)
            socket_port_map[sock] = port_num
        except OSError as e:
            logger.error(f"Could not bind to port {port_num}: {e}")
            return

    client_state = {}

    while True:
        readable, _, _ = select.select(sockets_to_watch, [], [])

        for sock in readable:
            data, addr = sock.recvfrom(1024)
            ip_address = addr[0]
            knocked_port = socket_port_map[sock]
            current_time = time.time()

            if ip_address not in client_state:
                client_state[ip_address] = [0, 0]

            current_index = client_state[ip_address][0]
            last_seen = client_state[ip_address][1]

            if current_index > 0 and (current_time - last_seen > window_seconds):
                logger.info(f"Timeout for {ip_address}. Resetting.")
                current_index = 0

            expected_port = sequence[current_index]

            if knocked_port == expected_port:
                current_index += 1
                client_state[ip_address] = [current_index, current_time]
                logger.info(f"Correct knock from {ip_address} on {knocked_port} (Stage {current_index}/{len(sequence)})")

                if current_index == len(sequence):
                    logger.info(f"Sequence complete for {ip_address}! Unlocking port.")
                    
                    t = threading.Thread(
                        target=handle_door_cycle,
                        args=(ip_address, protected_port)
                    )
                    t.start()
                    
                    client_state[ip_address] = [0, 0]
            else:
                logger.info(f"Wrong knock from {ip_address} on {knocked_port}. Resetting.")
                client_state[ip_address] = [0, 0]
                
                if knocked_port == sequence[0]:
                    client_state[ip_address] = [1, current_time]
                    logger.info(f"Restarting sequence for {ip_address}")

def handle_door_cycle(ip_address, protected_port, duration=30):
    """
    Opens the port, waits for 'duration' seconds, and then closes it.
    This runs in a separate thread so it doesn't block the main loop.
    """
    open_protected_port(ip_address, protected_port)
    
    logging.info(f"Door open for {ip_address}. Closing in {duration} seconds...")
    time.sleep(duration)
    
    close_protected_port(ip_address, protected_port)


def parse_args():
    parser = argparse.ArgumentParser(description="Port knocking server starter")
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
        "--window",
        type=float,
        default=DEFAULT_SEQUENCE_WINDOW,
        help="Seconds allowed to complete the sequence",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    setup_logging()

    try:
        initialize_firewall(args.protected_port)
        sequence = [int(port) for port in args.sequence.split(",")]
    except ValueError:
        raise SystemExit("Invalid sequence. Use comma-separated integers.")

    listen_for_knocks(sequence, args.window, args.protected_port)


def initialize_firewall(protected_port):
    """
    Ensure the firewall is in a secure state on startup.
    1. Flush existing rules (optional, but good for consistent state).
    2. Add the DROP rule for the protected port.
    """
    logging.info("Initializing firewall...")
    
    # 1. Flush rules (be careful if you have other rules!)
    # In this containerized environment, we assume we own the iptables.
    try:
        subprocess.run(["iptables", "-F"], check=True)
        logging.info("Flushed existing iptables rules.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to flush iptables: {e}")

    # 2. Add the DROP rule
    # -A INPUT -p tcp --dport <PORT> -j DROP
    command = [
        "iptables", "-A", "INPUT",
        "-p", "tcp",
        "--dport", str(protected_port),
        "-j", "DROP"
    ]
    
    try:
        subprocess.run(command, check=True)
        logging.info(f"Locked port {protected_port} (DROP rule added).")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to lock port {protected_port}: {e}")


if __name__ == "__main__":
    main()
