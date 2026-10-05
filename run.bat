@echo off
echo Starting BizFlow Development Servers (Django + FastAPI)...
py scripts\run_dev.py 2>nul || python scripts\run_dev.py 2>nul || "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" scripts\run_dev.py
pause
