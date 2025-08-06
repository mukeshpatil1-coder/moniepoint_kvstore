import socket
import threading
import argparse
from store.kv import KeyValueStore
from store.raft import RaftNode
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

def handle_client(conn, store, raft_node):
    with conn:
        while True:
            data = conn.recv(1024).decode()
            if not data: break
            parts = data.strip().split(" ", 2)
            cmd = parts[0].upper()

            if cmd in ["PUT", "DELETE", "BATCHPUT"] and raft_node.state != "leader":
                leader = raft_node.leader
                if leader:
                    conn.sendall(f"REDIRECT {leader}\n".encode())
                    continue

            if cmd == "PUT":
                key, value = parts[1], parts[2]
                raft_node.replicate_log(("PUT", key, value))
                store.put(key, value)
                conn.sendall(b"OK\n")
            elif cmd == "DELETE":
                key = parts[1]
                raft_node.replicate_log(("DEL", key, None))
                store.delete(key)
                conn.sendall(b"OK\n")
            elif cmd == "READ":
                value = store.read(parts[1])
                conn.sendall((value or "NOT_FOUND").encode() + b"\n")
            elif cmd == "BATCHPUT":
                items = eval(parts[1])
                for k, v in items:
                    raft_node.replicate_log(("PUT", k, v))
                store.batch_put(items)
                conn.sendall(b"OK\n")
            elif cmd == "RANGE":
                start, end = parts[1], parts[2]
                result = store.read_key_range(start, end)
                conn.sendall((str(result) + "\n").encode())

# def run_server(port, peers):
#     store = KeyValueStore()
#     raft_node = RaftNode(port, peers, store)
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.bind(("0.0.0.0", port))
#     s.listen(5)
#     print(f"KV Store running on port {port}...")
#     while True:
#         conn, _ = s.accept()
#         threading.Thread(target=handle_client, args=(conn, store, raft_node)).start()
    
def run_server(port, peers):
    store = KeyValueStore()
    store.set_config(port, peers)
    store.monitor_election()

    def health_server():
        def handler(*args, **kwargs):
            HealthCheckHandler(store, peers, *args, **kwargs)
        httpd = HTTPServer(("0.0.0.0", port + 100), handler)
        httpd.port = port
        print(f"Health endpoint running on port {port + 100}...")
        httpd.serve_forever()

    threading.Thread(target=health_server, daemon=True).start()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("0.0.0.0", port))
    s.listen(5)
    print(f"KV Store running on port {port}...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--peers", type=str, default="")
    args = parser.parse_args()
    peers = [( "127.0.0.1", int(p)) for p in args.peers.split(",") if p]
    run_server(args.port, peers)

class HealthCheckHandler(BaseHTTPRequestHandler):
    def __init__(self, store, peers, *args, **kwargs):
        self.store = store
        self.peers = peers
        super().__init__(*args, **kwargs)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(length)
        data = json.loads(data.decode())

        if self.path == "/heartbeat":
            self.store.receive_heartbeat(data.get("leader"), data.get("term"))
            self.send_response(200)
            self.end_headers()

        elif self.path == "/vote":
            vote_granted = self.store.handle_vote_request(data.get("candidate"), data.get("term"))
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"vote_granted": vote_granted}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            if self.store.is_leader:
                status = {
                    "status": "ok",
                    "port": self.server.port,
                    "role": "leader",
                    "leader": self.server.port,
                    "redirect": None
                }
            elif self.path == "/status":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "role": self.store.state,
                    "leader": self.store.leader_port,
                    "term": self.store.current_term
                }).encode())
            else:
                status = {
                    "status": "ok",
                    "port": self.server.port,
                    "role": "follower",
                    "leader": self.store.leader_port,
                    "redirect": f"http://localhost:{self.store.leader_port+100}/health" if self.store.leader_port else None
                }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(str(status).encode())
        else:
            self.send_response(404)
            self.end_headers()

    
