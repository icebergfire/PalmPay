#!/bin/bash
# PalmPay Terminal — Linux Launcher
# Supports Ubuntu, Debian, Fedora, Arch

clear
echo ""
echo "  ██████╗  █████╗ ██╗     ███╗   ███╗██████╗  █████╗ ██╗   ██╗"
echo "  ██╔══██╗██╔══██╗██║     ████╗ ████║██╔══██╗██╔══██╗╚██╗ ██╔╝"
echo "  ██████╔╝███████║██║     ██╔████╔██║██████╔╝███████║ ╚████╔╝ "
echo "  ██╔═══╝ ██╔══██║██║     ██║╚██╔╝██║██╔═══╝ ██╔══██║  ╚██╔╝ "
echo "  ██║     ██║  ██║███████╗██║ ╚═╝ ██║██║     ██║  ██║   ██║  "
echo "  ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝   ╚═╝  "
echo ""
echo "  Biometric Payment Terminal — Linux Edition"
echo "  ============================================"
echo ""

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Detect distro
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO=$ID
else
    DISTRO="unknown"
fi
echo "  Дистрибутив: $DISTRO"

# Install system deps if needed
install_system_deps() {
    echo "  [INFO] Установка системных зависимостей..."
    case $DISTRO in
        ubuntu|debian|linuxmint|pop)
            sudo apt-get update -qq
            sudo apt-get install -y python3 python3-pip python3-venv \
                libgl1-mesa-glx libglib2.0-0 libxcb-icccm4 libxcb-image0 \
                libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
                libxcb-xinerama0 libxkbcommon-x11-0 v4l-utils -q
            ;;
        fedora|rhel|centos)
            sudo dnf install -y python3 python3-pip python3-venv \
                mesa-libGL glib2 xcb-util-wm xcb-util-image \
                xcb-util-keysyms xcb-util-renderutil libxkbcommon-x11 -q
            ;;
        arch|manjaro|endeavouros)
            sudo pacman -Sy --noconfirm python python-pip \
                mesa glib2 xcb-util-wm xcb-util-image \
                xcb-util-keysyms xcb-util-renderutil libxkbcommon-x11
            ;;
        *)
            echo "  [WARN] Дистрибутив не определён, пропуск системных зависимостей"
            ;;
    esac
}

# Check Python
PY=""
for cmd in python3.11 python3.10 python3.9 python3; do
    if command -v $cmd &>/dev/null; then
        PY=$cmd
        break
    fi
done

if [ -z "$PY" ]; then
    echo "  [ОШИБКА] Python не найден! Устанавливаем..."
    install_system_deps
    PY=python3
fi

echo "  [OK] $($PY --version) найден"

# Check camera device
if ls /dev/video* 2>/dev/null | head -1 > /dev/null; then
    CAM=$(ls /dev/video* | head -1)
    echo "  [OK] Камера: $CAM"
    # Add user to video group if needed
    if ! groups | grep -q video; then
        echo "  [INFO] Добавление пользователя в группу video..."
        sudo usermod -aG video $USER
        echo "  [WARN] Может потребоваться перезайти в систему"
    fi
else
    echo "  [WARN] Камера не обнаружена — будет использован демо-режим"
fi

# Create virtualenv
if [ ! -d "venv" ]; then
    echo "  [1/3] Создание виртуального окружения..."
    $PY -m venv venv || {
        echo "  [INFO] Установка python3-venv..."
        install_system_deps
        $PY -m venv venv
    }
fi

source venv/bin/activate

# Install Python deps
python -c "import PyQt5" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "  [2/3] Установка Python зависимостей (~3-5 мин)..."
    pip install --upgrade pip -q
    pip install PyQt5 opencv-python mediapipe numpy -q
    pip install torch --index-url https://download.pytorch.org/whl/cpu -q
    echo "  [OK] Зависимости установлены"
else
    echo "  [2/3] Зависимости уже установлены"
fi

# Seed demo data
python -c "
import sys
sys.path.insert(0, '.')
from backend.database import Database
db = Database()
users = db.get_all_users()
if not users:
    print("  [OK] База данных готова — добавьте клиентов через меню Регистрация")
    print('  [3/3] Демо-данные загружены')
else:
    print('  [3/3] База данных: %d клиентов' % len(users))
"

# Set display for headless environments
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    export DISPLAY=:0
    echo "  [INFO] DISPLAY установлен в :0"
fi

echo ""
echo "  [ЗАПУСК] PalmPay Terminal..."
echo ""

python main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "  [ОШИБКА] Произошла ошибка запуска"
    echo "  Проверьте: export DISPLAY=:0"
    echo "  Или установите: sudo apt install libxcb-xinerama0"
    read -p "  Нажмите Enter..."
fi
