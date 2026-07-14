@echo off
cd /d "C:\Users\ZT\Desktop\Proyetos\entrenamiento iA"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
