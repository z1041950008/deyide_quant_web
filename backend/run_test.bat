@echo off
chcp 65001
setlocal enabledelayedexpansion

echo 正在激活虚拟环境...
call venv\Scripts\activate

echo 开始运行策略测试...
python test_strategy.py

pause 