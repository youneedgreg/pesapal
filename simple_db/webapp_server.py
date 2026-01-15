import http.server
import socketserver
import urllib.parse
from sql.executor import SQLExecutor
from core.database import Database
import json

PORT = 8000
DB_PATH = "webapp_db"

# Initialize DB
db = Database(DB_PATH)
executor = SQLExecutor(db)

# Ensure table exists
try:
    executor.execute("CREATE TABLE tasks (id int PK, content str)")
    executor.execute("INSERT INTO tasks (id, content) VALUES (1, 'Welcome to SimpleDB Web')")
except:
    pass # Already exists

class SimpleDBHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            tasks = db.get_table("tasks").select()
            
            html = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>SimpleDB Demo</title>
            <style>
                :root {
                    --bg-color: #ffffff;
                    --text-color: #333333;
                    --table-border: #dddddd;
                    --th-bg: #f2f2f2;
                    --form-bg: #f9f9f9;
                    --input-bg: #ffffff;
                    --input-border: #cccccc;
                }
                [data-theme="dark"] {
                    --bg-color: #1a1a1a;
                    --text-color: #e0e0e0;
                    --table-border: #444444;
                    --th-bg: #2d2d2d;
                    --form-bg: #2d2d2d;
                    --input-bg: #333333;
                    --input-border: #555555;
                }
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    max-width: 800px; 
                    margin: 2rem auto; 
                    background-color: var(--bg-color);
                    color: var(--text-color);
                    transition: all 0.3s ease;
                }
                h1 { text-align: center; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid var(--table-border); padding: 12px; text-align: left; }
                th { background-color: var(--th-bg); }
                form { margin-top: 30px; padding: 20px; background: var(--form-bg); border-radius: 8px; }
                input { 
                    padding: 8px; 
                    margin-right: 10px; 
                    background-color: var(--input-bg);
                    border: 1px solid var(--input-border);
                    color: var(--text-color);
                    border-radius: 4px;
                }
                button {
                    padding: 8px 16px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                button:hover { background-color: #0056b3; }
                .delete-btn { background-color: #dc3545; }
                .delete-btn:hover { background-color: #c82333; }
                
                .theme-toggle {
                    position: absolute;
                    top: 20px;
                    right: 20px;
                    background: none;
                    border: 1px solid var(--text-color);
                    color: var(--text-color);
                }
                .theme-toggle:hover {
                    background-color: var(--th-bg);
                }
            </style>
            </head>
            <body>
            <button class="theme-toggle" onclick="toggleTheme()">🌙 / ☀️</button>
            <h1>Simple DB To-Do List</h1>
            <table>
                <tr><th>ID</th><th>Task</th><th>Action</th></tr>
            """
            for t in tasks:
                 html += f"<tr><td>{t['id']}</td><td>{t['content']}</td><td><form action='/delete' method='POST' style='display:inline;margin:0;padding:0;background:none'><input type='hidden' name='id' value='{t['id']}'><button type='submit' class='delete-btn'>Delete</button></form></td></tr>"
            
            html += """
            </table>
            
            <form action="/add" method="POST">
                <h3>Add New Task</h3>
                <input type="number" name="id" placeholder="ID" required>
                <input type="text" name="content" placeholder="Task Content" required>
                <button type="submit">Add Task</button>
            </form>
            
            <script>
                function toggleTheme() {
                    const current = document.documentElement.getAttribute('data-theme');
                    const next = current === 'dark' ? 'light' : 'dark';
                    document.documentElement.setAttribute('data-theme', next);
                    localStorage.setItem('theme', next);
                }
                
                // Initialize theme
                const saved = localStorage.getItem('theme');
                if (saved) {
                    document.documentElement.setAttribute('data-theme', saved);
                } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                    document.documentElement.setAttribute('data-theme', 'dark');
                }
            </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        else:
            self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = urllib.parse.parse_qs(post_data)
        
        if self.path == "/add":
            t_id = params['id'][0]
            content = params['content'][0]
            try:
                # Basic protection for quotes in content
                content = content.replace("'", "''") 
                msg = executor.execute(f"INSERT INTO tasks (id, content) VALUES ({t_id}, '{content}')")
                print(f"ADD: {msg}")
            except Exception as e:
                print(f"Error adding: {e}")
                
        elif self.path == "/delete":
            t_id = params['id'][0]
            try:
                msg = executor.execute(f"DELETE FROM tasks WHERE id={t_id}")
                print(f"DELETE: {msg}")
            except Exception as e:
                print(f"Error deleting: {e}")

        # Redirect back only
        self.send_response(303)
        self.send_header('Location', '/')
        self.end_headers()

def run_server():
    print(f"Starting web server on port {PORT}...")
    # Reuse address to prevent 'Address already in use' errors on restart
    socketserver.TCPServer.allow_reuse_address = True
    http.server.HTTPServer(("", PORT), SimpleDBHandler).serve_forever()

if __name__ == "__main__":
    run_server()
