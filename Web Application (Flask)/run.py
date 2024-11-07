import subprocess
import webbrowser
from waitress import serve
from app import app  # Assuming your Flask app instance is named app in app.py

def run_server():
    serve(app, host='127.0.0.1', port=8000)

def open_browser():
    url = "http://127.0.0.1:8000"
    webbrowser.open(url, new=2)

if __name__ == "__main__":
    server_process = subprocess.Popen(["python", "-c", "from run import run_server; run_server()"])
    open_browser()
