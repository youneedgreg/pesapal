import os
import shutil
from core.database import Database
from core.table import Column

def test_core():
    # Setup
    if os.path.exists("test_db_data"):
        shutil.rmtree("test_db_data")
    
    db = Database("test_db_data")
    
    print("Creating table 'users'...")
    cols = [
        Column("id", "int", is_primary_key=True),
        Column("name", "str", nullable=False),
        Column("age", "int"),
        Column("email", "str", is_unique=True)
    ]
    db.create_table("users", cols)
    
    table = db.get_table("users")
    
    print("Inserting rows...")
    table.insert({"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com"})
    table.insert({"id": 2, "name": "Bob", "age": 25, "email": "bob@example.com"})
    
    print("Verifying select...")
    rows = table.select()
    assert len(rows) == 2
    assert rows[0]["name"] == "Alice"
    
    print("Verifying constraint (Unique)...")
    try:
        table.insert({"id": 3, "name": "Eve", "age": 28, "email": "alice@example.com"})
        print("FAIL: Unique constraint ignored")
    except ValueError as e:
        print(f"SUCCESS: Unique constraint caught ({e})")

    print("Verifying constraint (PK)...")
    try:
        table.insert({"id": 1, "name": "Duplicate Alice", "age": 99, "email": "new@example.com"})
        print("FAIL: PK constraint ignored")
    except ValueError as e:
        print(f"SUCCESS: PK constraint caught ({e})")

    print("Verifying update...")
    table.update({"age": 31}, lambda row: row["id"] == 1)
    row = table.select(lambda r: r["id"] == 1)[0]
    assert row["age"] == 31
    print("Update successful")

    print("Verifying persistence...")
    db.save_all()
    
    db2 = Database("test_db_data")
    table2 = db2.get_table("users")
    assert len(table2.rows) == 2
    print("Persistence successful")

    print("All core tests passed!")

if __name__ == "__main__":
    test_core()
