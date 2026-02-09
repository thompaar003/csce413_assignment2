# Honeypot Analysis

## Design Overview
This honeypot is a custom Python implementation using the `paramiko` library to simulate an SSH server. It is designed to look like a standard Ubuntu 22.04 LTS server running on port 22 inside the container, exposed as port 2222 on the host.

### Key Features:
-   **SSH Simulation**: Listens on port 22 (internally).
-   **Authentication**: Accepts any password to allow attackers to "succeed" and interact with the shell, maximizing data collection.
-   **Fake Shell**: Provides a limited set of commands (`ls`, `id`, `whoami`, `pwd`) to simulate a real environment. Unknown commands return a "command not found" error.
-   **Logging**: All events (connections, login attempts, commands) are logged to `logs/honeypot.log` in structured JSON format.

## Log Analysis
During testing, we simulated an attack using `test_attack.py` (Paramiko client). The logs captured detailed information about the attacker's activity.

### Observed Attack Pattern
1.  **Connection**: The attacker connected from `172.20.0.1` (the host network gateway from the container's perspective).
2.  **Authentication**: The attacker attempted to login as `root` with password `password123`. The honeypot successfully logged these credentials.
3.  **Command Execution**:
    -   `ls`: The honeypot listed fake directory contents: `Desktop`, `Documents`, etc.
    -   `pwd`: Returned `/root`.
    -   `whoami`: Returned `root`.
    -   `id`: Returned `uid=0(root) gid=0(root) groups=0(root)`.
    -   `cat /etc/passwd`: This command was not implemented in the fake shell, so it correctly returned `cat: command not found`.
    -   `exit`: Ended the session.

### Sample Log Entries
Below are actual log entries captured during the test:

```json
{"timestamp": "2026-02-09 22:35:27,555", "level": "INFO", "message": "CONNECTION_ESTABLISHED from 172.20.0.1:34040", "event_type": "CONNECTION_ESTABLISHED", "src_ip": "172.20.0.1", "src_port": 34040}
{"timestamp": "2026-02-09 22:35:27,667", "level": "INFO", "message": "LOGIN_ATTEMPT from 172.20.0.1:34040", "event_type": "LOGIN_ATTEMPT", "src_ip": "172.20.0.1", "src_port": 34040, "username": "root", "password": "password123"}
{"timestamp": "2026-02-09 22:35:28,669", "level": "INFO", "message": "COMMAND_EXECUTION from 172.20.0.1:34040", "event_type": "COMMAND_EXECUTION", "src_ip": "172.20.0.1", "src_port": 34040, "command": "ls"}
{"timestamp": "2026-02-09 22:35:32,670", "level": "INFO", "message": "COMMAND_EXECUTION from 172.20.0.1:34040", "event_type": "COMMAND_EXECUTION", "src_ip": "172.20.0.1", "src_port": 34040, "command": "cat /etc/passwd"}
```

## Conclusion
The honeypot successfully masquerades as an SSH server and captures detailed attacker activity, including source IP, credentials used, and commands executed. It fulfills the assignment requirements by simulating a real service, logging all attempts, and appearing convincing enough to elicit interaction.
