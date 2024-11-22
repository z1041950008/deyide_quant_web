@echo off
chcp 65001
setlocal enabledelayedexpansion

echo 正在激活虚拟环境...
call venv\Scripts\activate

echo 正在初始化数据库...
python -m app.models.init_db

pause 