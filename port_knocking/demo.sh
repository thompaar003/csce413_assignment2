#!/usr/bin/env bash

# Use 'docker compose' (newer) or 'docker-compose' (older) depending on your setup
DOCKER_CMD="docker compose"
CONTAINER_NAME="port_knocking"

TARGET_IP=${1:-172.20.0.20}
SEQUENCE=${2:-"1234,5678,9012"}
PROTECTED_PORT=${3:-2222}

echo "========================================================"
echo "[0/3] SETTING UP ENVIRONMENT (Resetting Container)"
echo "========================================================"

# 1. Clean Slate: Restart container to kill old processes
$DOCKER_CMD restart $CONTAINER_NAME
sleep 2 # Give it a moment to wake up

# 2. Flush existing rules to ensure a clean state
# The server now handles this on startup, so we don't strictly need to do it here,
# but restarting the container triggers the server's startup logic.
echo "      > Container restarted. Server should automatically lock the door."

# 3. Lock the Door: Drop all traffic to the protected port
# This is now handled by knock_server.py on startup.
echo "      > Verifying door is locked (Server logic)..."

# 4. Service is already running (secret_ssh), so we don't need to start a dummy one.
echo "      > Target service is secret_ssh on port $PROTECTED_PORT."

sleep 2
echo "      > Setup Complete. The door is locked and someone is home."
echo ""

echo "========================================================"
echo "[1/3] CHECKING LOCKED STATE"
echo "========================================================"
# -w 2 means timeout after 2 seconds
if nc -w 2 -z -v "$TARGET_IP" "$PROTECTED_PORT"; then
    echo "[-] FAIL: Port is open! It should be closed."
    exit 1
else
    echo "[+] PASS: Connection timed out."
fi

echo ""
echo "========================================================"
echo "[2/3] EXECUTING KNOCK SEQUENCE"
echo "========================================================"
# The client sends the UDP packets
python3 knock_client.py --target "$TARGET_IP" --sequence "$SEQUENCE"

echo ""
echo "========================================================"
echo "[3/3] CHECKING UNLOCKED STATE"
echo "========================================================"
# Check if we can connect now
if nc -w 2 -z -v "$TARGET_IP" "$PROTECTED_PORT"; then
    echo "[+] PASS: Connection Successful!"
else
    echo "[-] FAIL: Still timed out."
    exit 1
fi