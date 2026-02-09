# Honeypot Design Documentation

## Overview
This project implements a high-interaction SSH honeypot designed to simulate a vulnerable Linux server. The primary goal is to deceive attackers into believing they have gained unauthorized access to a system, thereby capturing their credentials, command history, and behavioral patterns.

## Architecture

The honeypot is built as a standalone Python application running within a Docker container. It leverages the `paramiko` library to implement the SSHv2 protocol, allowing for granular control over the authentication process and the simulated shell environment.

### Core Components

#### 1. SSH Server (`honeypot.py`)
-   **Library**: `paramiko` is used to handle the low-level SSH handshake and encryption details.
-   **Connection Handling**: The server listens on port 22 (inside the container) and accepts incoming TCP connections.
-   **Authentication**: The design decision was made to **accept all password-based login attempts**. This "low barrier to entry" strategy ensures that automated bots and attackers successfully "breach" the system, maximizing the amount of interaction data collected.
-   **Shell Simulation**: Instead of exposing a real system shell (which would be dangerous), the honeypot runs a simulated loop. It mimics a standard Ubuntu shell prompt and supports a limited subset of commands (`ls`, `pwd`, `whoami`, `id`, `exit`). This limits the attacker's ability to harm the host while still providing enough realism to capture subsequent commands.

#### 2. Logging and Alerting (`logger.py`)
-   **Data Structure**: Logs are written in **JSON format**. This was chosen over unstructured text logs to facilitate easier parsing and ingress into analysis tools (like ELK stack or simple Python scripts).
-   **Event Types**:
    -   `CONNECTION_ESTABLISHED`: Records the source IP and port.
    -   `LOGIN_ATTEMPT`: Captures the username and password used by the attacker.
    -   `COMMAND_EXECUTION`: specific commands typed into the fake shell.
    -   `CONNECTION_CLOSED`: Marks the end of a session.
-   **Alerting**: The system is designed to flag specific suspicious events (like rapid login failures, though in the current "accept all" configuration, this mainly tracks credential stuffing).

#### 3. Containerization (`Dockerfile`)
-   **Base Image**: `python:3.11-slim` provides a lightweight execution environment.
-   **Isolation**: Running in Docker ensures that even if the python process crashes or is exploited, the host system remains protected.
-   **Networking**: The container exposes port 22, which is mapped to a non-standard port (2222) on the host to emulate a shadow IT service or a secondary SSH daemon.

## Design Decisions & Trade-offs

-   **Simulation vs. Real OS**: We chose a specialized Python simulation over a real restricted shell or chroot jail.
    -   *Pros*: Complete control over what the attacker sees; impossible for the attacker to actually break out to the host OS via standard shell exploits; easy to capture keystrokes.
    -   *Cons*: Sophisticated attackers may realize the shell is fake if they run complex commands that aren't implemented (e.g., piping, specific flags for `ls`).
-   **Persistency**: The current design is stateless. Changes made by an attacker (like `touch file`) are not persisted. This was a trade-off for simplicity and recoverability—each session starts fresh.
-   **Port 2222**: Using a non-standard port on the host prevents conflict with the host's actual administrative SSH service and serves as a filter to attract scanners specifically looking for alternative SSH ports.

## Security Considerations
Since the honeypot processes untrusted input from the internet, the use of a memory-safe language (Python) and container isolation are critical security controls. The explicit "fake shell" parser prevents command injection attacks that might otherwise affect the underlying container OS.
