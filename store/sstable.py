import os
import json
import uuid

class SSTable:
    def __init__(self, data=None, filename=None):
        if filename:
            self.filename = filename
        else:
            self.filename = f"sstable_{uuid.uuid4().hex}.db"
            if data:
                with open(self.filename, "w") as f:
                    json.dump(data, f)

    def get(self, key):
        with open(self.filename, "r") as f:
            data = json.load(f)
            return data.get(key)

    def range_query(self, start, end):
        with open(self.filename, "r") as f:
            data = json.load(f)
            return {k: v for k, v in data.items() if start <= k <= end}

    @staticmethod
    def compact(sstables):
        merged_data = {}
        for sstable in sstables:
            with open(sstable.filename, "r") as f:
                data = json.load(f)
                merged_data.update({k: v for k, v in data.items() if v is not None})
        new_sstable = SSTable(merged_data)
        for sstable in sstables:
            os.remove(sstable.filename)
        return new_sstable
