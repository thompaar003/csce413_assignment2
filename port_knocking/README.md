## Port Knocking Implementation

### Concept: The State Machine
The Port Knocking server is implemented as a **State Machine** rather than a simple packet sniffer. This ensures that the specific sequence of ports must be hit in the *exact order* and within a specific *time window*.

The logic mimics a "Switchboard Operator" monitoring multiple lines (ports) simultaneously:
1.  **Idle State:** The server listens on UDP ports `1234`, `5678`, and `9012` using `select` to handle non-blocking I/O.
2.  **Tracking Progress:** When an IP "knocks" (sends a packet) on a port, the server checks an internal registry:
    * **Correct Knock:** If the port matches the expected next step for that IP, the user's "Level" is incremented.
    * **Wrong Knock:** If the port is incorrect, the user's progress is reset to Level 0.
    * **Timeout:** If the user takes too long between knocks (exceeding the `window`), their progress is reset.
3.  **Unlock:** Once the final port in the sequence is hit, the server triggers the firewall modification.

### Firewall Management
The server interacts with the Linux Kernel's netfilter firewall using `subprocess` calls to `iptables`.
* **Opening:** When a sequence is verified, a rule is **inserted** (`-I`) at the top of the `INPUT` chain, specifically allowing TCP traffic on Port 2222 for the knocker's source IP only.
* **Automatic Closing:** To maintain security, a separate thread (`threading.Timer`) is spawned immediately after unlocking. This thread waits for a set duration and then **deletes** (`-D`) the allow rule, effectively locking the door behind the user.