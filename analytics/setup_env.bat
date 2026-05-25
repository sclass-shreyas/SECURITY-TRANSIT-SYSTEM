@echo off
setlocal

call ..\detection\venv\Scripts\activate
python -m pip install -r requirements.txt

echo Analytics module ready. Run: uvicorn main:app --host 0.0.0.0 --port 8000
endlocal
