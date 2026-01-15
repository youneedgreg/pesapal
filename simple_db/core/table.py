from typing import Any, Dict, List, Optional, Union
import json
import os

class Column:
    def __init__(self, name: str, col_type: str, is_primary_key: bool = False, is_unique: bool = False, nullable: bool = True):
        self.name = name
        self.col_type = col_type  # 'int', 'str', 'float', 'bool'
        self.is_primary_key = is_primary_key
        self.is_unique = is_unique
        self.nullable = nullable

    def to_dict(self):
        return {
            "name": self.name,
            "col_type": self.col_type,
            "is_primary_key": self.is_primary_key,
            "is_unique": self.is_unique,
            "nullable": self.nullable
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        return Column(
            name=data["name"],
            col_type=data["col_type"],
            is_primary_key=data.get("is_primary_key", False),
            is_unique=data.get("is_unique", False),
            nullable=data.get("nullable", True)
        )

class Table:
    def __init__(self, name: str, columns: List[Column]):
        self.name = name
        self.columns = {col.name: col for col in columns}
        self.rows: List[Dict[str, Any]] = []
        self.indexes: Dict[str, Dict[Any, int]] = {} # index_name -> {value -> row_idx in self.rows}
        # Ideally indexes point to a stable ID, but for simplicity we'll point to list index
        # NOTE: Deletion will require re-building indexes or using a stable row ID map.
        # Let's use a simple auto-increment generic ID for internal tracking if needed, 
        # or just linear scan for MVP and rebuild.
        # Better approach for MVP: Indexes map value -> List[row_index]. 
        
        self._init_indexes()

    def _init_indexes(self):
        self.indexes = {}
        for col in self.columns.values():
            if col.is_primary_key or col.is_unique:
                self.indexes[col.name] = {}

    def _rebuild_indexes(self):
        self._init_indexes()
        for idx, row in enumerate(self.rows):
            for col_name in self.indexes:
                val = row.get(col_name)
                if val is not None:
                    self.indexes[col_name][val] = idx

    def insert(self, row_data: Dict[str, Any]):
        # Validate schema and constraints
        final_row = {}
        
        for col_name, col in self.columns.items():
            val = row_data.get(col_name)
            
            # Type check (basic)
            if val is not None:
                if col.col_type == 'int' and not isinstance(val, int):
                    try: val = int(val)
                    except: raise ValueError(f"Column {col_name} expects int")
                elif col.col_type == 'float' and not isinstance(val, (float, int)):
                     try: val = float(val)
                     except: raise ValueError(f"Column {col_name} expects float")
                elif col.col_type == 'str' and not isinstance(val, str):
                    val = str(val)
                elif col.col_type == 'bool' and not isinstance(val, bool):
                    val = bool(val)

            # Constraint Check: Not Null
            if val is None and not col.nullable:
                 raise ValueError(f"Column {col_name} cannot be null")
            
            # Constraint Check: Primary Key / Unique
            if (col.is_primary_key or col.is_unique) and val is not None:
                if val in self.indexes[col_name]:
                    raise ValueError(f"Duplicate value '{val}' for unique column '{col_name}'")

            final_row[col_name] = val

        # Insert
        self.rows.append(final_row)
        new_idx = len(self.rows) - 1
        
        # Update Indexes
        for col_name, idx_map in self.indexes.items():
            val = final_row.get(col_name)
            if val is not None:
                idx_map[val] = new_idx

    def select(self, where_func=None):
        if where_func is None:
            return self.rows
        return [row for row in self.rows if where_func(row)]

    def delete(self, where_func):
        # This is expensive as it requires rebuilding indexes
        # But required for correctness if we track by list index
        initial_len = len(self.rows)
        self.rows = [row for row in self.rows if not where_func(row)]
        if len(self.rows) != initial_len:
            self._rebuild_indexes()
        return initial_len - len(self.rows)

    def update(self, updates: Dict[str, Any], where_func):
        updated_count = 0
        for i, row in enumerate(self.rows):
            if where_func(row):
                # We essentially need to re-validate constraints if we update PK/Unique
                # Simpler MVP: Don't allow updating PKs? Or just check explicitly.
                
                # Check constraints for updates
                for col_name, new_val in updates.items():
                    col = self.columns.get(col_name)
                    if not col: continue
                    if col.is_primary_key or col.is_unique:
                        if new_val != row.get(col_name):
                            if new_val in self.indexes[col_name]:
                                raise ValueError(f"Duplicate value '{new_val}' for unique column '{col_name}'")

                # Apply updates
                for key, val in updates.items():
                    if key in self.columns:
                        row[key] = val
                updated_count += 1
        
        if updated_count > 0:
            self._rebuild_indexes()
        return updated_count

    def to_dict(self):
        return {
            "name": self.name,
            "columns": [c.to_dict() for c in self.columns.values()],
            "rows": self.rows
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]):
        cols = [Column.from_dict(c) for c in data["columns"]]
        table = Table(data["name"], cols)
        table.rows = data["rows"]
        table._rebuild_indexes()
        return table
