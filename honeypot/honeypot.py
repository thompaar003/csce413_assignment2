#!/usr/bin/env python3
"""SSH Honeypot using Paramiko."""

import socket
import threading
import paramiko
import time
import os
from logger import log_event, log_alert

HOST_KEY_FILE = "/etc/ssh/ssh_host_rsa_key"
PORT = 22

# Generate a host key if it doesn't exist (for local testing mostly, Docker handles this)
if not os.path.exists(HOST_KEY_FILE):
    # Fallback/Test key generation - in production Dockerfile should handle this or mount it
    pass 

class HoneyPotServer(paramiko.ServerInterface):
    """Paramiko Server Interface implementation for the honeypot."""
    
    def __init__(self, client_ip, client_port):
        self.event = threading.Event()
        self.client_ip = client_ip
        self.client_port = client_port

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        log_event("LOGIN_ATTEMPT", self.client_ip, self.client_port, 
                  username=username, password=password)
        
        # Simulate successful login for common credentials to encourage interaction
        # or simple let everyone in for maximum data gathering
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

def handle_connection(client, addr):
    """Handle a new incoming SSH connection."""
    client_ip, client_port = addr
    print(f"Connection from {client_ip}:{client_port}")
    log_event("CONNECTION_ESTABLISHED", client_ip, client_port)
    
    try:
        transport = paramiko.Transport(client)
        
        # Load host key
        # Try to use a persistent key location in /app if possible, or fallback gracefully
        key_path = "/app/ssh_host_rsa_key"
        if not os.path.exists(key_path):
             # Try /etc/ssh...
             if os.path.exists(HOST_KEY_FILE):
                 key_path = HOST_KEY_FILE
             else:
                 print("Generating temporary host key...")
                 key = paramiko.RSAKey.generate(2048)
                 key.write_private_key_file(key_path)
        
        host_key = paramiko.RSAKey(filename=key_path)
        transport.add_server_key(host_key)
        
        server = HoneyPotServer(client_ip, client_port)
        try:
            transport.start_server(server=server)
        except paramiko.SSHException:
            print("SSH negotiation failed.")
            return

        # Wait for auth
        chan = transport.accept(20)
        if chan is None:
            print("No channel.")
            return

        server.event.wait(10)
        if not server.event.is_set():
            print("Client never requested a shell.")
            chan.close()
            return

        chan.send("Welcome to Ubuntu 22.04.2 LTS (GNU/Linux 5.15.0-72-generic x86_64)\r\n\r\n")
        chan.send(" * Documentation:  https://help.ubuntu.com\r\n")
        chan.send(" * Management:     https://landscape.canonical.com\r\n")
        chan.send(" * Support:        https://ubuntu.com/advantage\r\n\r\n")
        
        # Simple shell loop
        prompt = "root@server:~# "
        chan.send(prompt)
        
        buff = ""
        while True:
            try:
                recv = chan.recv(1024)
                if not recv:
                    break
                
                # Echo back (simple pty simulation) - IMPORTANT: Do not echo newlines locally if client sends them?
                # Actually, standard terminals echo locally often, but raw mode needs remote echo.
                # Simplest is just to echo whatever is received.
                data = recv.decode('utf-8', errors='ignore')
                chan.send(data) 
                
                buff += data
                
                # Process lines
                while "\n" in buff or "\r" in buff:
                    # Find the first newline
                    n_pos = buff.find("\n")
                    r_pos = buff.find("\r")
                    
                    if n_pos != -1 and (r_pos == -1 or n_pos < r_pos):
                        end_pos = n_pos
                    else:
                        end_pos = r_pos
                        
                    cmd_line = buff[:end_pos].strip()
                    # Skip the newline char(s)
                    if end_pos + 1 < len(buff) and buff[end_pos:end_pos+2] == "\r\n":
                        buff = buff[end_pos+2:]
                    else:
                        buff = buff[end_pos+1:]
                        
                    if cmd_line:
                        log_event("COMMAND_EXECUTION", client_ip, client_port, command=cmd_line)
                        
                        # Handle simulated commands
                        response = ""
                        if cmd_line == "exit":
                             chan.close()
                             return
                        elif cmd_line == "ls":
                             response = "Desktop  Documents  Downloads  Music  Pictures  Public  Templates  Videos\r\n"
                        elif cmd_line == "pwd":
                             response = "/root\r\n"
                        elif cmd_line == "whoami":
                             response = "root\r\n"
                        elif cmd_line == "id":
                             response = "uid=0(root) gid=0(root) groups=0(root)\r\n"
                        elif cmd_line.startswith("cd"):
                             pass # ignore
                        else:
                             response = f"{cmd_line.split()[0]}: command not found\r\n"
                            
                        # Send response (if any) then prompt
                        # Need to ensure we send a newline before response if the user just hit enter
                        chan.send("\r\n" + response + prompt)
                    else:
                        # Empty line (just enter)
                        chan.send("\r\n" + prompt)

            except Exception as e:
                print(f"Shell error: {e}")
                break

        log_event("CONNECTION_CLOSED", client_ip, client_port)
        chan.close()

    except Exception as e:
        print(f"Connection error: {e}")
        log_event("ERROR", client_ip, client_port, error=str(e))

def run_honeypot():
    """Main loop."""
    print(f"Starting honeypot on port {PORT}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('0.0.0.0', PORT))
    sock.listen(100)

    while True:
        try:
            client, addr = sock.accept()
            t = threading.Thread(target=handle_connection, args=(client, addr))
            t.start()
        except Exception as e:
            print(f"Accept error: {e}")

if __name__ == "__main__":
    run_honeypot()
