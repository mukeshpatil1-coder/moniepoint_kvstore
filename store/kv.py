from .wal import WriteAheadLog
from .sstable import SSTable
from collections import OrderedDict
import threading
import time
import random
import requests

class KeyValueStore:
    def __init__(self):
        self.store = {}
        self.wal = WriteAheadLog()
        self.state = "follower"
        self.leader_port = None
        self.current_term = 0
        self.voted_for = None
        self.peers = []
        self.port = None
        self.election_timeout = random.uniform(3, 5)
        self.last_heartbeat = time.time()
        self.op_count = 0
        self.snapshot_threshold = 100  # Take snapshot every 100 ops
        self.recover()


    def set_config(self, port, peers):
        self.port = port
        self.peers = peers

    def set_leader(self, port, term):
        self.state = "leader" if port == self.port else "follower"
        self.leader_port = port
        self.current_term = term
        if self.state == "leader":
            print(f"[ELECTION] Node {port} became LEADER for term {term}")
            self.broadcast_heartbeat()
        else:
            print(f"[ELECTION] Node {port} is the new LEADER for term {term} (this node is FOLLOWER)")

    def broadcast_heartbeat(self):
        def task():
            while self.state == "leader":
                for peer in self.peers:
                    try:
                        requests.post(f"http://localhost:{peer+100}/heartbeat",
                                      json={"leader": self.port, "term": self.current_term},
                                      timeout=0.5)
                    except:
                        continue
                time.sleep(2)
        threading.Thread(target=task, daemon=True).start()

    def receive_heartbeat(self, leader_port, term):
        if term >= self.current_term:
            self.state = "follower"
            self.current_term = term
            self.voted_for = None
            self.leader_port = leader_port
            self.last_heartbeat = time.time()

    def request_vote(self):
        self.current_term += 1
        self.voted_for = self.port
        self.wal.append_state(self.current_term, self.voted_for)
        self.state = "candidate"
        votes = 1
        print(f"[ELECTION] Node {self.port} requesting votes for term {self.current_term}...")
        for peer in self.peers:
            try:
                resp = requests.post(f"http://localhost:{peer+100}/vote",
                                     json={"candidate": self.port, "term": self.current_term},
                                     timeout=0.5)
                if resp.status_code == 200 and resp.json().get("vote_granted"):
                    votes += 1
            except:
                continue

        if votes > (len(self.peers) + 1) // 2:
            self.set_leader(self.port, self.current_term)
        else:
            print(f"[ELECTION] Node {self.port} failed to get majority (votes={votes}). Retrying...")
            self.state = "follower"
            self.voted_for = None

    def monitor_election(self):
        def monitor():
            while True:
                time.sleep(1)
                if self.state != "leader" and (time.time() - self.last_heartbeat > self.election_timeout):
                    self.request_vote()
        threading.Thread(target=monitor, daemon=True).start()

    def handle_vote_request(self, candidate, term):
        if term > self.current_term:
            self.current_term = term
            self.voted_for = None
            self.state = "follower"

        if (self.voted_for is None or self.voted_for == candidate) and term >= self.current_term:
            self.voted_for = candidate
            self.wal.append_state(self.current_term, self.voted_for)
            return True
        return False
    
    def recover(self):
        for op, key, value in self.wal.replay():
            if op == "SNAPSHOT":
                self.store = key  # key contains snapshot dict
            elif op == "STATE":
                self.current_term = key
                self.voted_for = value
            elif op == "PUT":
                self.store[key] = value
            elif op == "DELETE":
                self.store.pop(key, None)

    def _check_snapshot(self):
        self.op_count += 1
        if self.op_count >= self.snapshot_threshold:
            print(f"[SNAPSHOT] Creating snapshot at {self.op_count} operations")
            self.wal.create_snapshot(self.store, self.current_term, self.voted_for)
            self.op_count = 0

    def put(self, key, value):
        self.store[key] = value
        self.wal.append("PUT", key, value)
        self._check_snapshot()

    def read(self, key):
        if key in self.memtable:
            return self.memtable[key]
        for sstable in reversed(self.sstables):
            val = sstable.get(key)
            if val is not None:
                return val
        return None

    def read_key_range(self, start, end):
        result = {k: v for k, v in self.memtable.items() if start <= k <= end}
        for sstable in self.sstables:
            result.update(sstable.range_query(start, end))
        return result

    def batch_put(self, items):
        for k, v in items:
            self.put(k, v)

    def delete(self, key):
        if key in self.store:
            del self.store[key]
            self.wal.append("DELETE", key)
            self._check_snapshot()
            
    def flush_to_sstable(self):
        sstable = SSTable(self.memtable)
        self.sstables.append(sstable)
        self.memtable.clear()
        self.wal.clear()
        if len(self.sstables) > 3:
            self.compact_sstables()

    def compact_sstables(self):
        new_sstable = SSTable.compact(self.sstables)
        self.sstables = [new_sstable]
