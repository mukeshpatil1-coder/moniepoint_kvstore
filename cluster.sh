#!/bin/bash

# =========================
# Moniepoint KV Cluster Script
# =========================

#!/bin/bash

VENV=".venv"
PORT_BASE=6000
NUM_NODES=3
PYTHON="$VENV/bin/python3"

# ---------------------------
# Helper: Get peer list for a node
# ---------------------------
get_peers() {
    local port=$1
    local peers=""
    for ((i=0; i<$NUM_NODES; i++)); do
        local p=$((PORT_BASE + i))
        if [ "$p" -ne "$port" ]; then
            if [ -z "$peers" ]; then
                peers="$p"
            else
                peers="$peers,$p"
            fi
        fi
    done
    echo "$peers"
}

# Ensure Python virtual environment
check_dependencies() {
    echo "Checking Python dependencies..."
    if [ ! -d "$VENV" ]; then
        echo "Creating virtual environment..."
        python3 -m venv $VENV
    fi
    source $VENV/bin/activate
    pip install --quiet requests flask || true
    echo "✅ All dependencies are satisfied (using .venv)."
}

# Start the cluster
start_cluster() {
    echo "Starting KV cluster on ports: $(seq -s ', ' $PORT_BASE $((PORT_BASE + NUM_NODES - 1)))"
    for ((i=0; i<$NUM_NODES; i++)); do
        local port=$((PORT_BASE+i))
        local peers=$(get_peers $port)
        $PYTHON server.py --port $port --peers $peers > "node_$port.log" 2>&1 &
        sleep 1
        echo "KV Store running on port $port..."
    done
    echo "Cluster started successfully."
}

# Stop the cluster
stop_cluster() {
    echo "Stopping KV cluster..."
    pkill -f "server.py" || true
    echo "Cluster stopped."
}

# Restart the cluster
restart_cluster() {
    stop_cluster
    check_dependencies
    # If 5000 is busy, shift to 6000 series
    if lsof -i :5000 > /dev/null 2>&1; then
        echo "Port 5000 is busy. Switching to 6000-series ports..."
        PORT_BASE=6000
    fi
    # Kill any hanging processes
    for ((i=0; i<$NUM_NODES; i++)); do
        kill -9 $(lsof -ti tcp:$((PORT_BASE+i))) 2>/dev/null || true
    done
    start_cluster
}

# Check cluster health
check_health() {
    echo "=== CLUSTER HEALTH CHECK ==="
    for ((i=0; i<$NUM_NODES; i++)); do
        local port=$((PORT_BASE+i))
        STATUS=$(curl -s "http://localhost:$port/health" || echo "")
        ROLE=$(echo "$STATUS" | grep -o '"role":"[^"]*' | cut -d'"' -f4)

        if [[ -z "$ROLE" ]]; then
            echo "Node $port: ❌ Down. Restarting..."
            pkill -f "server.py --port $port" || true
            peers=$(get_peers $port)
            $PYTHON server.py --port $port --peers $peers > "node_$port.log" 2>&1 &
            echo "✅ Node $port restarted successfully."
        else
            echo "Node $port: ✅ $ROLE"
        fi
    done
}

# Main commands
case "$1" in
    start)
        check_dependencies
        start_cluster
        ;;
    stop)
        stop_cluster
        ;;
    restart)
        restart_cluster
        ;;
    health)
        check_dependencies
        check_health
        ;;
    *)
        echo "Usage: ./cluster.sh {start|stop|restart|health}"
        ;;
esac




# Default ports
LEADER_PORT=5000
FOLLOWER1_PORT=5001
FOLLOWER2_PORT=5002

check_port() {
  if lsof -i :$1 > /dev/null; then
    return 1
  else
    return 0
  fi
}

set_ports() {
  if ! check_port $LEADER_PORT; then
    echo "Port $LEADER_PORT is busy. Switching to 6000-series ports..."
    LEADER_PORT=6000
    FOLLOWER1_PORT=6001
    FOLLOWER2_PORT=6002
  fi
}

start_cluster() {
  set_ports
  echo "Starting KV cluster on ports: $LEADER_PORT, $FOLLOWER1_PORT, $FOLLOWER2_PORT"
  pkill -f server.py 2>/dev/null

  python3 server.py --port $LEADER_PORT --peers $FOLLOWER1_PORT,$FOLLOWER2_PORT &
  sleep 1
  python3 server.py --port $FOLLOWER1_PORT --peers $LEADER_PORT,$FOLLOWER2_PORT &
  sleep 1
  python3 server.py --port $FOLLOWER2_PORT --peers $LEADER_PORT,$FOLLOWER1_PORT &
  echo "Cluster started successfully."
}

stop_cluster() {
  echo "Stopping KV cluster..."
  pkill -f server.py
  echo "Cluster stopped."
}

restart_cluster() {
    echo "Stopping KV cluster..."
    pkill -f server.py || true
    echo "Cluster stopped."

    echo "Starting KV cluster on ports: 6000, 6001, 6002"
    for port in 6000 6001 6002; do
        python3 server.py --port $port --peers $(get_peers $port) &
        echo "KV Store running on port $port..."
    done
    sleep 2
    echo "Cluster started successfully."
}


status_cluster() {
  echo "Checking cluster status..."
  lsof -i :$LEADER_PORT || echo "Leader port $LEADER_PORT is free."
  lsof -i :$FOLLOWER1_PORT || echo "Follower 1 port $FOLLOWER1_PORT is free."
  lsof -i :$FOLLOWER2_PORT || echo "Follower 2 port $FOLLOWER2_PORT is free."
}

case "$1" in
  start)
    start_cluster
    ;;
  stop)
    stop_cluster
    ;;
  restart)
    restart_cluster
    ;;
  status)
    status_cluster
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
esac
