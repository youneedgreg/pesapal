from typing import Any, Dict, List, Callable
from core.database import Database
from core.table import Column
from sql.parser import SQLParser


class SQLExecutor:
    def __init__(self, db: Database):
        self.db = db
        self.parser = SQLParser()

    def execute(self, sql: str) -> str:
        try:
            cmd = self.parser.parse(sql)
        except ValueError as e:
            return f"Syntax Error: {e}"

        try:
            if cmd["type"] == "CREATE":
                return self._exec_create(cmd)
            elif cmd["type"] == "INSERT":
                return self._exec_insert(cmd)
            elif cmd["type"] == "SELECT":
                return self._exec_select(cmd)
            elif cmd["type"] == "UPDATE":
                return self._exec_update(cmd)
            elif cmd["type"] == "DELETE":
                return self._exec_delete(cmd)
        except Exception as e:
            return f"Error: {e}"
        
        return "Unknown command"

    def _exec_create(self, cmd):
        cols = []
        for c in cmd["columns"]:
            cols.append(Column(
                c["name"], 
                c["type"], 
                is_primary_key=c["pk"],
                is_unique=c["unique"]
            ))
        self.db.create_table(cmd["table"], cols)
        return f"Table '{cmd['table']}' created."

    def _exec_insert(self, cmd):
        table = self.db.get_table(cmd["table"])
        table.insert(cmd["data"])
        self.db.save_table(table.name)
        return "1 row inserted."

    def _exec_select(self, cmd):
        table = self.db.get_table(cmd["table"])
        
        # Handle JOIN
        # For simplified join, we do a nested loop or hash join if possible
        # We need to return rows combined
        
        rows = table.rows
        
        # Simplistic filtering
        if cmd["where"]:
            rows = [r for r in rows if self._eval_where(r, cmd["where"])]

        # Handle JOIN
        if cmd["join"]:
            join_table_name = cmd["join"]["table"]
            join_table = self.db.get_table(join_table_name)
            condition = cmd["join"]["on"]
            
            # Very basic nested loop join
            joined_rows = []
            for row_a in rows:
                for row_b in join_table.rows:
                    if self._eval_join_condition(row_a, row_b, table.name, join_table_name, condition):
                         # Merge rows
                         merged = {**row_a, **{f"{join_table_name}.{k}": v for k,v in row_b.items()}}
                         joined_rows.append(merged)
            rows = joined_rows

        # Projection
        if cmd["columns"]:
            projected = []
            for r in rows:
                new_r = {}
                for col in cmd["columns"]:
                    # Handle aliasing or table prefixes if needed
                    val = r.get(col)
                    if val is None and "." in col:
                        # try lookup with table prefix or without
                        t, c = col.split('.')
                        # If table prefix matches main table, look for c
                        if t == table.name:
                            val = r.get(c)
                        # If key in row is actually prefixed (joined table)
                        elif col in r:
                            val = r[col]
                    new_r[col] = val 
                projected.append(new_r)
            rows = projected
            
        return self._format_result(rows)

    def _exec_update(self, cmd):
        table = self.db.get_table(cmd["table"])
        count = table.update(cmd["updates"], lambda r: self._eval_where(r, cmd["where"]) if cmd["where"] else True)
        self.db.save_table(table.name)
        return f"{count} rows updated."

    def _exec_delete(self, cmd):
        table = self.db.get_table(cmd["table"])
        count = table.delete(lambda r: self._eval_where(r, cmd["where"]) if cmd["where"] else True)
        self.db.save_table(table.name)
        return f"{count} rows deleted."

    def _eval_where(self, row: Dict[str, Any], where_clause: str) -> bool:
        # Extremely naive eval: "col = val" or "col > val"
        # Security risk: eval() - but for a toy RDBMS challenge it's the standard shortcut
        # To be safer/cleaner, we should parse the condition.
        # Let's support simple "col = val" parsing without eval()
        
        parts = where_clause.split('=')
        if len(parts) == 2:
            col = parts[0].strip()
            val_str = parts[1].strip()
            
            # Determine if val_str is a string literal or number
            val = self.parser._clean_val(val_str)
            
            return row.get(col) == val
            
        return False # Fallback or complex condition not supported

    def _eval_join_condition(self, row_a, row_b, name_a, name_b, condition):
        # condition e.g. "users.id = posts.user_id"
        left, right = condition.split('=')
        left = left.strip()
        right = right.strip()
        
        def get_val(ref):
            if '.' in ref:
                t, c = ref.split('.')
                if t == name_a: return row_a.get(c)
                if t == name_b: return row_b.get(c)
            else:
                return row_a.get(ref) # Default to left table?
        
        return get_val(left) == get_val(right)

    def _format_result(self, rows: List[Dict[str, Any]]) -> str:
        if not rows:
            return "Empty set"
        
        # Simple ASCII table
        headers = list(rows[0].keys())
        lines = []
        lines.append("\t".join(headers))
        for r in rows:
            lines.append("\t".join([str(r.get(h, 'NULL')) for h in headers]))
        return "\n".join(lines)
