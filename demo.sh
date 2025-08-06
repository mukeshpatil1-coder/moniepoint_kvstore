#!/bin/bash

# ===========================
# Moniepoint KV Store Demo Script
# ===========================

echo "🚀 Starting Moniepoint KV Store End-to-End Demo..."

# ---------------------------
# 1. Clean up old logs
# ---------------------------
echo "🧹 Cleaning up old logs..."
rm -f watchdog.log

# ---------------------------
# 2. Stop any existing watchdog
# ---------------------------
echo "🛑 Stopping existing watchdog..."
pkill -f watchdog.sh &>/dev/null || true

# ---------------------------
# 3. Restart cluster
# ---------------------------
echo "🔄 Restarting cluster..."
./cluster.sh stop
./cluster.sh start

# ---------------------------
# 4. Wait for leader election
# ---------------------------
echo "⏳ Waiting for leader election..."
sleep 3

# ---------------------------
# 5. Health check
# ---------------------------
echo "🔍 Checking cluster health..."
./cluster.sh health

# ---------------------------
# 6. Run KV operations
# ---------------------------
echo "📝 Running KV operations..."

echo "➡️ PUT key=name value=Mukesh"
curl -s -X POST http://localhost:6000/put -H "Content-Type: application/json" -d '{"key":"name","value":"Mukesh"}' | jq .

echo "➡️ READ key=name"
curl -s "http://localhost:6000/get?key=name" | jq .

echo "➡️ BATCH PUT keys=k1,k2,k3 values=v1,v2,v3"
curl -s -X POST http://localhost:6000/batch_put -H "Content-Type: application/json" \
    -d '{"keys":["k1","k2","k3"],"values":["v1","v2","v3"]}' | jq .

echo "➡️ READ RANGE k1 to k3"
curl -s "http://localhost:6000/range?start=k1&end=k3" | jq .

echo "➡️ DELETE key=name"
curl -s -X DELETE "http://localhost:6000/delete?key=name" | jq .

# ---------------------------
# 7. Simulate leader failover
# ---------------------------
echo "⚡ Simulating leader failover (killing port 6000)..."
pkill -f "server.py --port 6000" || true
sleep 3

echo "🔁 Checking cluster health after failover..."
./cluster.sh health

# ---------------------------
# 8. Start watchdog
# ---------------------------
echo "🔍 Starting watchdog for continuous monitoring..."
nohup ./watchdog.sh > watchdog.log 2>&1 &

echo "✅ Watchdog running in background (logging to watchdog.log)"
echo "✅ Demo completed! Cluster is running and auto-healing."
