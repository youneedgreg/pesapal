import os
import json
from typing import Dict, Optional
from .table import Table, Column

class Database:
    def __init__(self, storage_dir: str = "db_data"):
        self.storage_dir = storage_dir
        self.tables: Dict[str, Table] = {}
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
        self.load_metadata()

    def create_table(self, name: str, columns: list[Column]):
        if name in self.tables:
            raise ValueError(f"Table {name} already exists.")
        table = Table(name, columns)
        self.tables[name] = table
        self.save_table(name)

    def get_table(self, name: str) -> Table:
        if name not in self.tables:
            # Try to load if not in memory but potentially on disk (though load_metadata should handle this)
            raise ValueError(f"Table {name} not found.")
        return self.tables[name]
    
    def drop_table(self, name: str):
        if name in self.tables:
            del self.tables[name]
            # Remove file
            path = os.path.join(self.storage_dir, f"{name}.json")
            if os.path.exists(path):
                os.remove(path)

    def save_table(self, name: str):
        if name in self.tables:
            table = self.tables[name]
            path = os.path.join(self.storage_dir, f"{name}.json")
            with open(path, 'w') as f:
                json.dump(table.to_dict(), f, indent=2)

    def load_metadata(self):
        # Load all .json files in storage_dir as tables
        if not os.path.exists(self.storage_dir):
            return
        
        files = os.listdir(self.storage_dir)
        for f in files:
            if f.endswith(".json"):
                path = os.path.join(self.storage_dir, f)
                try:
                    with open(path, 'r') as file_handle:
                        data = json.load(file_handle)
                        table = Table.from_dict(data)
                        self.tables[table.name] = table
                except Exception as e:
                    print(f"Failed to load table from {f}: {e}")

    def save_all(self):
        for name in self.tables:
            self.save_table(name)
