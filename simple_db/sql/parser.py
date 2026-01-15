import re
from typing import Any, Dict, List, Optional

class SQLParser:
    def parse(self, sql: str) -> Dict[str, Any]:
        sql = sql.strip().rstrip(';')
        # Naive tokenziation by space might fail on string literals with spaces.
        # But for simple RDBMS without complex string parser, we'll try regex matching for whole commands.
        
        # CREATE TABLE
        match = re.match(r"CREATE\s+TABLE\s+(\w+)\s*\((.+)\)", sql, re.IGNORECASE | re.DOTALL)
        if match:
            return self._parse_create(match)

        # INSERT INTO
        match = re.match(r"INSERT\s+INTO\s+(\w+)\s*\((.+)\)\s*VALUES\s*\((.+)\)", sql, re.IGNORECASE | re.DOTALL)
        if match:
            return self._parse_insert(match)

        # SELECT
        # Supports: SELECT col1, col2 FROM table [JOIN table2 ON cond] [WHERE cond]
        match = re.match(r"SELECT\s+(.+)\s+FROM\s+(\w+)(.*)", sql, re.IGNORECASE | re.DOTALL)
        if match:
            return self._parse_select(match)

        # UPDATE
        match = re.match(r"UPDATE\s+(\w+)\s+SET\s+(.+?)(?:\s+WHERE\s+(.+))?$", sql, re.IGNORECASE | re.DOTALL)
        if match:
            return self._parse_update(match)

        # DELETE
        match = re.match(r"DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+))?$", sql, re.IGNORECASE | re.DOTALL)
        if match:
            return self._parse_delete(match)

        raise ValueError(f"Unsupported or invalid SQL: {sql}")

    def _parse_create(self, match) -> Dict[str, Any]:
        table_name = match.group(1)
        columns_def = match.group(2)
        columns = []
        # Split by comma but careful about potential futures like size (int(11)) - though we stick to simple types
        raw_cols = [c.strip() for c in columns_def.split(',')]
        for rc in raw_cols:
            parts = rc.split()
            col_name = parts[0]
            col_type = parts[1]
            is_pk = 'PK' in parts or 'PRIMARY KEY' in rc.upper()
            is_unique = 'UNIQUE' in parts
            columns.append({
                "name": col_name,
                "type": col_type,
                "pk": is_pk,
                "unique": is_unique
            })
        return {"type": "CREATE", "table": table_name, "columns": columns}

    def _parse_insert(self, match) -> Dict[str, Any]:
        table_name = match.group(1)
        cols_str = match.group(2)
        vals_str = match.group(3)
        
        columns = [c.strip() for c in cols_str.split(',')]
        
        # Handle values - naive split by comma, doesn't support strings with commas yet properly
        # For a "Simple RDBMS" challenge this is usually acceptable unless specified otherwise
        # Better: use regex or a generic csv splitter
        values = [self._clean_val(v.strip()) for v in vals_str.split(',')]
        
        if len(columns) != len(values):
            raise ValueError("Column count doesn't match value count")
            
        return {"type": "INSERT", "table": table_name, "data": dict(zip(columns, values))}

    def _clean_val(self, val_str: str) -> Any:
        if (val_str.startswith("'") and val_str.endswith("'")) or (val_str.startswith('"') and val_str.endswith('"')):
            return val_str[1:-1]
        try:
            if '.' in val_str:
                return float(val_str)
            return int(val_str)
        except:
            return val_str

    def _parse_select(self, match) -> Dict[str, Any]:
        columns_str = match.group(1).strip()
        table_name = match.group(2)
        rest = match.group(3).strip()
        
        columns = [c.strip() for c in columns_str.split(',')]
        if columns == ['*']: 
            columns = None
            
        join = None
        where = None
        
        # Check for JOIN
        join_match = re.search(r"JOIN\s+(\w+)\s+ON\s+(.+?)(?:\s+WHERE\s+(.+))?$", rest, re.IGNORECASE)
        if join_match:
            join = {
                "table": join_match.group(1),
                "on": join_match.group(2)
            }
            if join_match.group(3):
                where = join_match.group(3)
        else:
            # Check for WHERE without join
            where_match = re.search(r"WHERE\s+(.+)", rest, re.IGNORECASE)
            if where_match:
                where = where_match.group(1)
                
        return {
            "type": "SELECT",
            "table": table_name,
            "columns": columns,
            "join": join,
            "where": where
        }

    def _parse_update(self, match) -> Dict[str, Any]:
        table_name = match.group(1)
        set_str = match.group(2)
        where_str = match.group(3)
        
        updates = {}
        for pair in set_str.split(','):
            k, v = pair.split('=')
            updates[k.strip()] = self._clean_val(v.strip())
            
        return {
            "type": "UPDATE",
            "table": table_name,
            "updates": updates,
            "where": where_str
        }

    def _parse_delete(self, match) -> Dict[str, Any]:
        table_name = match.group(1)
        where_str = match.group(2)
        return {
            "type": "DELETE",
            "table": table_name,
            "where": where_str
        }
