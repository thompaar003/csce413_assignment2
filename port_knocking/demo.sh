#!/usr/bin/env bash

# Use 'docker compose' (newer) or 'docker-compose' (older) depending on your setup
DOCKER_CMD="docker compose"
CONTAINER_NAME="port_knocking"

TARGET_IP=${1:-172.20.0.40}
SEQUENCE=${2:-"1234,5678,9012"}
PROTECTED_PORT=${3:-2222}

echo "========================================================"
echo "[0/4] SETTING UP ENVIRONMENT (Resetting Container)"
echo "========================================================"

# 1. Clean Slate: Restart container to kill old processes and flush iptables
$DOCKER_CMD restart $CONTAINER_NAME
sleep 2 # Give it a moment to wake up

# 2. Lock the Door: Drop all traffic to the protected port
echo "      > Locking the door (iptables DROP rule)..."
$DOCKER_CMD exec -T $CONTAINER_NAME iptables -A INPUT -p tcp --dport "$PROTECTED_PORT" -j DROP

# 3. Start Dummy Service: Run a Python web server in the background (-d)
echo "      > Starting dummy service (Python HTTP Server)..."
$DOCKER_CMD exec -d $CONTAINER_NAME python3 -m http.server "$PROTECTED_PORT"

sleep 2
echo "      > Setup Complete. The door is locked and someone is home."
echo ""

echo "========================================================"
echo "[1/4] CHECKING LOCKED STATE (Expect Timeout)"
echo "========================================================"
# -w 2 means timeout after 2 seconds
if nc -w 2 -z -v "$TARGET_IP" "$PROTECTED_PORT"; then
    echo "[-] FAIL: Port is open! It should be locked."
    exit 1
else
    echo "[+] PASS: Connection timed out. The door is effectively locked."
fi

echo ""
echo "========================================================"
echo "[2/4] EXECUTING KNOCK SEQUENCE"
echo "========================================================"
# The client sends the UDP packets
python3 knock_client.py --target "$TARGET_IP" --sequence "$SEQUENCE"

echo ""
echo "========================================================"
echo "[3/4] CHECKING UNLOCKED STATE (Expect Success)"
echo "========================================================"
# Check if we can connect now
if nc -w 2 -z -v "$TARGET_IP" "$PROTECTED_PORT"; then
    echo "[+] PASS: Connection Successful! The door opened."
else
    echo "[-] FAIL: Still timed out. The door did not open."
    exit 1
fi