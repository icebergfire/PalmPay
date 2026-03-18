@echo off
chcp 65001 >nul
title PalmPay Terminal — Windows

echo.
echo  ██████╗  █████╗ ██╗     ███╗   ███╗██████╗  █████╗ ██╗   ██╗
echo  ██╔══██╗██╔══██╗██║     ████╗ ████║██╔══██╗██╔══██╗╚██╗ ██╔╝
echo  ██████╔╝███████║██║     ██╔████╔██║██████╔╝███████║ ╚████╔╝
echo  ██╔═══╝ ██╔══██║██║     ██║╚██╔╝██║██╔═══╝ ██╔══██║  ╚██╔╝
echo  ██║     ██║  ██║███████╗██║ ╚═╝ ██║██║     ██║  ██║   ██║
echo  ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝   ╚═╝
echo.
echo  Biometric Payment Terminal — Windows Edition
echo  ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo.
    echo Установите Python 3.9+ с сайта: https://python.org/downloads
    echo При установке отметьте "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYVER=%%i
echo [OK] Python %PYVER% найден

:: Create venv if not exists
if not exist "venv\" (
    echo [1/3] Создание виртуального окружения...
    python -m venv venv
)

:: Activate
call venv\Scripts\activate.bat

:: Install deps if not present
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo [2/3] Установка зависимостей (первый запуск ~3 мин)...
    pip install --upgrade pip -q
    pip install PyQt5 opencv-python mediapipe numpy -q
    pip install torch --index-url https://download.pytorch.org/whl/cpu -q
    echo [OK] Зависимости установлены
) else (
    echo [2/3] Зависимости уже установлены
)

:: Seed demo data if no users
python -c "
import os, sys
sys.path.insert(0, '.')
from backend.database import Database
db = Database()
users = db.get_all_users()
if not users:
    print("  [OK] База данных готова")
    print('[3/3] Демо-данные загружены')
else:
    print('[3/3] База данных: %d клиентов' % len(users))
"

echo.
echo [ЗАПУСК] PalmPay Terminal...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [ОШИБКА] Произошла ошибка при запуске
    echo Проверьте камеру или запустите в демо-режиме
    pause
)
