@echo off
chcp 65001
setlocal enabledelayedexpansion

echo 正在激活虚拟环境...
call venv\Scripts\activate

echo 正在启动应用...
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

pause 