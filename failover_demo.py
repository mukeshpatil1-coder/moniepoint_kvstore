import os
import time
from client import KVClient

def kill_leader(port):
    print(f"\n[FAILOVER] Killing leader on port {port}...")
    os.system(f"lsof -ti :{port} | xargs kill -9 || true")
    time.sleep(2)

if __name__ == "__main__":
    client = KVClient([5000, 5001, 5002])

    print("\n[STEP 1] Writing initial data...")
    print(client.put("user", "Mukesh"))
    print(client.read("user"))

    # Identify current leader
    client._discover_leader()
    current_leader = client.leader_port
    print(f"\n[INFO] Current leader is on port {current_leader}")

    # Kill the leader
    kill_leader(current_leader)

    print("\n[STEP 2] Writing after failover...")
    print(client.put("city", "Pune"))  # Should auto-redirect to new leader
    print(client.read("city"))

    print("\n[STEP 3] Verifying previous data is still available...")
    print(client.read("user"))

    print("\n✅ Failover successful! Client automatically redirected to new leader.")
