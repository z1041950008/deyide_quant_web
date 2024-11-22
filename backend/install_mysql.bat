@echo off
chcp 65001
setlocal enabledelayedexpansion

echo 正在激活虚拟环境...
call venv\Scripts\activate

echo 正在安装 MySQL 相关依赖...
pip install pymysql
pip install mysql-connector-python

echo 安装完成！
pause 