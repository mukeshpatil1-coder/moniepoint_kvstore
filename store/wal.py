import os
import json

class WriteAheadLog:
    def __init__(self, filename="wal.log", snapshot_file="snapshot.json"):
        self.filename = filename
        self.snapshot_file = snapshot_file
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                f.write("")
        if not os.path.exists(self.snapshot_file):
            with open(self.snapshot_file, "w") as f:
                json.dump({}, f)

    def append(self, operation, key=None, value=None):
        with open(self.filename, "a") as f:
            if value is not None:
                f.write(f"{operation},{key},{value}\n")
            elif key is not None:
                f.write(f"{operation},{key}\n")
            else:
                f.write(f"{operation}\n")

    def append_state(self, term, voted_for):
        with open(self.filename, "a") as f:
            f.write(f"STATE,{term},{voted_for if voted_for else 'None'}\n")

    def replay(self):
        if os.path.exists(self.snapshot_file):
            with open(self.snapshot_file, "r") as f:
                snapshot = json.load(f)
                yield "SNAPSHOT", snapshot, None

        with open(self.filename, "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if not parts or len(parts) < 1:
                    continue
                if parts[0] == "STATE" and len(parts) >= 3:
                    yield "STATE", int(parts[1]), None if parts[2] == "None" else int(parts[2])
                elif len(parts) == 3:
                    yield parts[0], parts[1], parts[2]
                elif len(parts) == 2:
                    yield parts[0], parts[1], None

    def create_snapshot(self, data, term, voted_for):
        # Write snapshot
        with open(self.snapshot_file, "w") as f:
            json.dump(data, f)

        # Reset WAL but keep state
        with open(self.filename, "w") as f:
            f.write(f"STATE,{term},{voted_for if voted_for else 'None'}\n")

    def clear(self):
        self.file.close()
        open(self.filename, "w").close()
        self.file = open(self.filename, "a+", buffering=1)

