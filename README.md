# Moniepoint Distributed KV Store

A lightweight distributed key-value (KV) store designed for **low latency**, **high throughput**, **crash recovery**, and **automatic failover**.

---

## 🚀 Features

- **Low Latency**: Optimized in-memory hash map caching.
- **High Throughput**: Batched writes, concurrent socket handling.
- **Handles Large Datasets**: Write-Ahead Log (WAL) with periodic snapshots.
- **Crash Friendliness**: Fast WAL replay on recovery.
- **Predictable Under Load**: Leader-based coordination, watchdog restarts.
- **Replication**: Data replicated across nodes.
- **Failover**: Automatic node recovery and leader re-election.

---

## 🏗 Architecture

```
                +-------------------+
                |   Client (CLI)    |
                +---------+---------+
                          |
                 +--------v---------+
                 |   Leader Node    |
                 |  (Write/Coord)   |
                 +--------+---------+
                          |
        --------------------------------------
        |                |                   |
+-------v-------+ +------v--------+ +--------v-------+
|  Follower 1   | |  Follower 2   | |   Follower 3   |
+---------------+ +---------------+ +----------------+

- Replication via HTTP/Socket
- WAL-based persistence
- Watchdog monitors node health
```

## Project Structure
moniepoint_kvstore/
├── server.py
├── store/
│   ├── kv.py
│   ├── wal.py
├── cluster.sh
├── demo.sh
├── watchdog.sh
├── requirements.txt
└── README.md

---

## 📦 Requirements

- Python 3.9+
- Virtualenv
- `requests` library
- Unix-like OS (Mac/Linux)

---

## ⚡ Installation

```bash
git clone https://github.com/mukeshpatil1-coder/moniepoint_kvstore.git
cd moniepoint_kvstore
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## ▶ Usage

### Start the cluster
```bash
./cluster.sh start
```

### Check health
```bash
./cluster.sh health
```

### Run full demo
```bash
./demo.sh
```

This will:
1. Start 3-node cluster.
2. Elect leader.
3. Perform `PUT`, `GET`, `BATCH PUT`, `RANGE READ`, `DELETE` operations.
4. Simulate leader failover and auto-recovery.

---

## ✅ Design Choices vs Requirements

| Requirement                                   | Implementation                                                                                     |
|-----------------------------------------------|-----------------------------------------------------------------------------------------------------|
| **Low latency**                               | In-memory caching with WAL.                                                                        |
| **High throughput**                           | Batched WAL + concurrent socket handling.                                                          |
| **Large dataset support**                     | WAL + periodic snapshots.                                                                          |
| **Crash friendliness**                        | WAL replay on restart.                                                                             |
| **Predictable behavior**                      | Leader-based coordination and backpressure.                                                        |
| **Replication** *(bonus)*                     | Peer-to-peer write replication.                                                                    |
| **Failover** *(bonus)*                        | Health watchdog + auto-restart + leader re-election.                                               |

---

## 🛡️ Failover Workflow

1. Leader node crashes.
2. Watchdog detects failure.
3. Node restarts.
4. Leader re-election happens automatically.
5. Cluster resumes operation without manual intervention.

---

## 🧪 Testing

To run the end-to-end demo with failover:
```bash
./demo.sh
```

Expected behavior:
- All nodes start and elect a leader.
- KV operations succeed.
- Leader failover occurs.
- Cluster auto-heals.

If you see an error about PEP 668 (externally managed environment), you can install dependencies using:
```bash
pip install -r requirements.txt --break-system-packages
```

---

## ▶️ Running the Cluster

Start the cluster:
```bash
./cluster.sh start
```

Stop the cluster:
```bash
./cluster.sh stop
```

Restart the cluster:
```bash
./cluster.sh restart
```

Check health:
```bash
./cluster.sh health
```

---

## 🧪 Running End-to-End Demo

The `demo.sh` script automates the following:
- Cleans old logs
- Starts the cluster
- Detects leader
- Runs KV operations (PUT, READ, DELETE, BATCH PUT, RANGE)
- Simulates leader failover
- Verifies new leader election
- Starts watchdog monitoring

Run the demo:
```bash
./demo.sh
```

---

## 🔑 KV Store API

### 1. PUT Key-Value
```bash
curl -X PUT "http://localhost:6000/kv?key=name&value=Mukesh"
```

### 2. GET Key
```bash
curl "http://localhost:6000/kv?key=name"
```

### 3. DELETE Key
```bash
curl -X DELETE "http://localhost:6000/kv?key=name"
```

### 4. BATCH PUT
```bash
curl -X POST "http://localhost:6000/kv/batch" -H "Content-Type: application/json" -d '{"data":{"k1":"v1","k2":"v2","k3":"v3"}}'
```

### 5. RANGE READ
```bash
curl "http://localhost:6000/kv/range?start=k1&end=k3"
```

---

## ⚡ Leader Failover Simulation

To manually simulate failover:
```bash
lsof -ti tcp:6000 | xargs kill -9
./cluster.sh health
```

The cluster will elect a new leader automatically.

---

## 🛠 Watchdog

The watchdog monitors the cluster and restarts failed nodes:
```bash
./watchdog.sh
```

It also runs automatically at the end of the demo.

---

## ✅ Troubleshooting

### Address already in use
If you see:
```
OSError: [Errno 48] Address already in use
```
Clean up processes:
```bash
pkill -f server.py
```

### No leader detected
Ensure all nodes are running:
```bash
./cluster.sh restart
./cluster.sh health
```

### Missing dependencies
Activate the virtual environment:
```bash
source .venv/bin/activate
```

Then install requirements:
```bash
pip install -r requirements.txt
```

---

## 🏆 Demo Workflow
1. `./demo.sh` → Starts cluster, detects leader, performs KV ops
2. Simulates leader failover → new leader elected
3. Watchdog runs → ensures cluster stays healthy

---

## References
- [Bigtable Design](https://static.googleusercontent.com/media/research.google.com/en//archive/bigtable-osdi06.pdf)
- [Bitcask](https://riak.com/assets/bitcask-intro.pdf)
- [LSM Tree](https://www.cs.umb.edu/~poneil/lsmtree.pdf)
- [Raft Consensus](https://web.stanford.edu/~ouster/cgi-bin/papers/raft-atc14.pdf)
- [Paxos](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf)

## 📄 License

MIT License
