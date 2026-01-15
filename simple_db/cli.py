import sys
from sql.executor import SQLExecutor
from core.database import Database

def run_repl(db_path="db_data"):
    print("SimpleDB v1.0")
    print(f"Data directory: {db_path}")
    print("Type 'exit' or 'quit' to close.")
    
    db = Database(db_path)
    executor = SQLExecutor(db)
    
    while True:
        try:
            sql = input("SQL> ")
            if sql.lower() in ["exit", "quit"]:
                break
            if not sql.strip():
                continue
                
            result = executor.execute(sql)
            print(result)
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except EOFError:
            break

if __name__ == "__main__":
    db_path = "db_data"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    run_repl(db_path)
