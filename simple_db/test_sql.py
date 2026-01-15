import os
import shutil
from core.database import Database
from sql.executor import SQLExecutor

def test_sql():
    if os.path.exists("test_db_sql"):
        shutil.rmtree("test_db_sql")
    
    db = Database("test_db_sql")
    executor = SQLExecutor(db)

    print("Testing CREATE TABLE...")
    res = executor.execute("CREATE TABLE users (id int PK, name str, age int)")
    print(res)
    assert "created" in res

    print("Testing INSERT...")
    res = executor.execute("INSERT INTO users (id, name, age) VALUES (1, 'Alice', 30)")
    print(res)
    assert "inserted" in res
    executor.execute("INSERT INTO users (id, name, age) VALUES (2, 'Bob', 25)")
    executor.execute("INSERT INTO users (id, name, age) VALUES (3, 'Charlie', 35)")

    print("Testing SELECT...")
    res = executor.execute("SELECT id, name FROM users")
    print(res)
    assert "Alice" in res
    assert "Bob" in res

    print("Testing SELECT WHERE...")
    res = executor.execute("SELECT name FROM users WHERE id=2")
    print(res)
    assert "Bob" in res
    assert "Alice" not in res

    print("Testing UPDATE...")
    res = executor.execute("UPDATE users SET age=31 WHERE id=1")
    print(res)
    res = executor.execute("SELECT age FROM users WHERE id=1")
    assert "31" in res

    print("Testing DELETE...")
    res = executor.execute("DELETE FROM users WHERE id=3")
    print(res)
    res = executor.execute("SELECT name FROM users")
    assert "Charlie" not in res

    # JOIN TEST
    print("Testing JOIN...")
    executor.execute("CREATE TABLE posts (id int PK, user_id int, title str)")
    executor.execute("INSERT INTO posts (id, user_id, title) VALUES (101, 1, 'Alice Post')")
    executor.execute("INSERT INTO posts (id, user_id, title) VALUES (102, 2, 'Bob Post')")

    res = executor.execute("SELECT users.name, posts.title FROM users JOIN posts ON users.id = posts.user_id")
    print("JOIN Result:\n", res)
    assert "Alice" in res
    assert "Alice Post" in res
    assert "Bob" in res 
    assert "Bob Post" in res

    print("SQL Tests Passed!")

if __name__ == "__main__":
    test_sql()
