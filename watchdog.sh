#!/bin/bash

VENV=".venv"
PORT_BASE=6000
NUM_NODES=3
PYTHON="$VENV/bin/python3"
LOG_FILE="watchdog.log"

# Ensure Python virtual environment
check_dependencies() {
    if [ ! -d "$VENV" ]; then
        echo "Creating virtual environment..."
        python3 -m venv $VENV
    fi
    source $VENV/bin/activate
    pip install --quiet requests flask || true
}

# Get peers for a node
get_peers() {
    local port=$1
    local peers=""
    for ((i=0; i<$NUM_NODES; i++)); do
        local p=$((PORT_BASE+i))
        if [ $p -ne $port ]; then
            if [ -z "$peers" ]; then
                peers="$p"
            else
                peers="$peers,$p"
            fi
        fi
    done
    echo "$peers"
}

# Monitor and restart only unhealthy nodes
monitor_cluster() {
    while true; do
        echo "=== WATCHDOG CHECK $(date) ===" >> "$LOG_FILE"
        for ((i=0; i<$NUM_NODES; i++)); do
            local port=$((PORT_BASE+i))
            STATUS=$(curl -s "http://localhost:$port/health" || echo "")
            ROLE=$(echo "$STATUS" | grep -o '"role":"[^"]*' | cut -d'"' -f4)

            if [[ -z "$ROLE" ]]; then
                echo "[$(date)] Node $port: ❌ Down. Restarting..." >> "$LOG_FILE"
                pkill -f "server.py --port $port" || true
                peers=$(get_peers $port)
                $PYTHON server.py --port $port --peers $peers > "node_$port.log" 2>&1 &
                echo "[$(date)] ✅ Node $port restarted successfully." >> "$LOG_FILE"
            else
                echo "[$(date)] Node $port: ✅ Healthy ($ROLE)" >> "$LOG_FILE"
            fi
        done
        sleep 5
    done
}

check_dependencies
monitor_cluster
