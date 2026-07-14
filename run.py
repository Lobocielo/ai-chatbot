import subprocess
import sys
import time
import os
import webbrowser

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("========================================")
print("   AI Chatbot - Iniciando todo...")
print("========================================")
print()

# Start backend
print("[1/2] Iniciando backend (FastAPI)...")
backend = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# Wait for backend
import requests
backend_ready = False
for i in range(30):
    time.sleep(2)
    try:
        r = requests.get("http://127.0.0.1:8000/health", timeout=1)
        if r.status_code == 200:
            print("   Backend listo!")
            backend_ready = True
            break
    except:
        pass

if not backend_ready:
    print("   ERROR: Backend no arranco")
    backend.terminate()
    sys.exit(1)

# Start frontend
print("[2/2] Iniciando frontend (Next.js)...")
frontend = subprocess.Popen(
    [sys.executable, "-m", "npm", "run", "dev"],
    cwd=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend"),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    shell=True
)

# Wait for frontend
frontend_ready = False
for i in range(30):
    time.sleep(2)
    try:
        r = requests.get("http://localhost:3000", timeout=1)
        if r.status_code == 200:
            print("   Frontend listo!")
            frontend_ready = True
            break
    except:
        pass

if not frontend_ready:
    print("   Frontend puede estar cargando, abriendo navegador de todas formas...")

print()
print("========================================")
print("   TODO INICIADO!")
print("========================================")
print()
print("   Frontend: http://localhost:3000")
print("   Backend:  http://localhost:8000")
print()
print("   Presiona Ctrl+C para cerrar todo")
print("========================================")

webbrowser.open("http://localhost:3000")

try:
    backend.wait()
except KeyboardInterrupt:
    print("\nCerrando...")
    backend.terminate()
    frontend.terminate()
    print("Todo cerrado.")
