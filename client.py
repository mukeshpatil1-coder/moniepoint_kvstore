import socket
import json
import requests

class KVClient:
    def __init__(self, nodes):
        """
        nodes: List of node base ports. Example: [5000, 5001, 5002]
        """
        self.nodes = nodes
        self.leader_port = None

    def _discover_leader(self):
        """Find leader from any available node."""
        for port in self.nodes:
            try:
                resp = requests.get(f"http://localhost:{port+100}/health", timeout=1)
                if resp.status_code == 200:
                    data = json.loads(resp.text.replace("'", '"'))
                    if data.get("role") == "leader":
                        self.leader_port = data["leader"]
                        return
                    elif data.get("leader"):
                        self.leader_port = data["leader"]
                        return
            except Exception:
                continue
        raise Exception("No available leader found!")

    def _send_command(self, port, command):
        """Send a command to a specific node."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", port))
        s.sendall((command + "\n").encode())
        data = s.recv(4096).decode().strip()
        s.close()
        return data

    def _ensure_leader(self):
        if not self.leader_port:
            self._discover_leader()

    def put(self, key, value):
        self._ensure_leader()
        try:
            return self._send_command(self.leader_port, f"PUT {key} {value}")
        except Exception:
            self.leader_port = None
            self._ensure_leader()
            return self.put(key, value)

    def read(self, key):
        self._ensure_leader()
        try:
            return self._send_command(self.leader_port, f"READ {key}")
        except Exception:
            self.leader_port = None
            self._ensure_leader()
            return self.read(key)

    def delete(self, key):
        self._ensure_leader()
        try:
            return self._send_command(self.leader_port, f"DELETE {key}")
        except Exception:
            self.leader_port = None
            self._ensure_leader()
            return self.delete(key)

    def batch_put(self, kv_pairs):
        """
        kv_pairs: List of tuples [(k1, v1), (k2, v2)]
        """
        self._ensure_leader()
        batch_str = " ".join([f"{k}:{v}" for k, v in kv_pairs])
        try:
            return self._send_command(self.leader_port, f"BATCHPUT {batch_str}")
        except Exception:
            self.leader_port = None
            self._ensure_leader()
            return self.batch_put(kv_pairs)

    def range_read(self, start_key, end_key):
        self._ensure_leader()
        try:
            return self._send_command(self.leader_port, f"RANGE {start_key} {end_key}")
        except Exception:
            self.leader_port = None
            self._ensure_leader()
            return self.range_read(start_key, end_key)
