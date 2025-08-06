import threading
import time
import random
import socket
import json

class RaftNode:
    def __init__(self, node_id, peers, kvstore):
        self.node_id = node_id
        self.peers = peers
        self.kvstore = kvstore
        self.state = "follower"
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        self.leader = None
        self.election_timeout = random.uniform(3, 5)
        self.last_heartbeat = time.time()
        threading.Thread(target=self.election_timer, daemon=True).start()

    def election_timer(self):
        while True:
            time.sleep(0.5)
            if self.state != "leader" and (time.time() - self.last_heartbeat) > self.election_timeout:
                self.start_election()

    def start_election(self):
        self.state = "candidate"
        self.current_term += 1
        self.voted_for = self.node_id
        votes = 1
        for peer in self.peers:
            if self.request_vote(peer):
                votes += 1
        if votes > (len(self.peers) + 1) // 2:
            self.state = "leader"
            self.leader = self.node_id
            threading.Thread(target=self.send_heartbeats, daemon=True).start()

    def request_vote(self, peer):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect(peer)
            msg = json.dumps({"type": "vote_request", "term": self.current_term})
            sock.sendall(msg.encode())
            resp = sock.recv(1024).decode()
            sock.close()
            return resp == "vote_granted"
        except:
            return False

    def send_heartbeats(self):
        while self.state == "leader":
            for peer in self.peers:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    sock.connect(peer)
                    msg = json.dumps({"type": "heartbeat", "leader": self.node_id})
                    sock.sendall(msg.encode())
                    sock.close()
                except:
                    pass
            time.sleep(1)

    def replicate_log(self, entry):
        self.log.append(entry)
        for peer in self.peers:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect(peer)
                msg = json.dumps({"type": "replicate", "entry": entry})
                sock.sendall(msg.encode())
                sock.close()
            except:
                pass

    def handle_message(self, msg):
        if msg["type"] == "heartbeat":
            self.last_heartbeat = time.time()
            self.leader = msg["leader"]
            self.state = "follower"
        elif msg["type"] == "vote_request":
            if self.voted_for is None or self.voted_for == msg["term"]:
                self.voted_for = msg["term"]
                return "vote_granted"
            return "vote_denied"
        elif msg["type"] == "replicate":
            self.log.append(msg["entry"])
            op, key, value = msg["entry"]
            if op == "PUT":
                self.kvstore.put(key, value)
            elif op == "DEL":
                self.kvstore.delete(key)
        return "ok"
