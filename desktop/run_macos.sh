#!/bin/bash
# PalmPay Terminal — macOS Launcher
# Supports Intel (x86_64) and Apple Silicon (M1/M2/M3)

clear
echo ""
echo "  ██████╗  █████╗ ██╗     ███╗   ███╗██████╗  █████╗ ██╗   ██╗"
echo "  ██╔══██╗██╔══██╗██║     ████╗ ████║██╔══██╗██╔══██╗╚██╗ ██╔╝"
echo "  ██████╔╝███████║██║     ██╔████╔██║██████╔╝███████║ ╚████╔╝ "
echo "  ██╔═══╝ ██╔══██║██║     ██║╚██╔╝██║██╔═══╝ ██╔══██║  ╚██╔╝ "
echo "  ██║     ██║  ██║███████╗██║ ╚═╝ ██║██║     ██║  ██║   ██║  "
echo "  ╚═╝     ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝╚═╝     ╚═╝  ╚═╝   ╚═╝  "
echo ""
echo "  Biometric Payment Terminal — macOS Edition"
echo "  ============================================"
echo ""

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Detect architecture
ARCH=$(uname -m)
echo "  Архитектура: $ARCH"

# Check Python
PY=""
for cmd in python3.11 python3.10 python3.9 python3; do
    if command -v $cmd &>/dev/null; then
        PY=$cmd
        break
    fi
done

if [ -z "$PY" ]; then
    echo ""
    echo "  [ОШИБКА] Python не найден!"
    echo ""
    echo "  Установите через Homebrew:"
    echo "    /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo "    brew install python"
    echo ""
    read -p "  Нажмите Enter для выхода..."
    exit 1
fi

PYVER=$($PY --version 2>&1)
echo "  [OK] $PYVER найден"

# Camera permission check (macOS 10.14+)
echo "  [INFO] При первом запуске macOS запросит доступ к камере."
echo "         Нажмите 'Разрешить' в системном диалоге."
echo ""

# Create virtualenv
if [ ! -d "venv" ]; then
    echo "  [1/3] Создание виртуального окружения..."
    $PY -m venv venv
fi

source venv/bin/activate

# Install dependencies
python -c "import PyQt5" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "  [2/3] Установка зависимостей (~3-5 мин)..."
    pip install --upgrade pip -q

    if [ "$ARCH" = "arm64" ]; then
        # Apple Silicon — use specific compatible versions
        echo "  [INFO] Обнаружен Apple Silicon (M1/M2/M3)"
        pip install PyQt5 -q
        pip install opencv-python-headless -q
        pip install mediapipe -q
        pip install numpy -q
        # PyTorch for Apple Silicon with MPS support
        pip install torch torchvision -q
    else
        # Intel Mac
        echo "  [INFO] Обнаружен Intel Mac"
        pip install PyQt5 opencv-python mediapipe numpy -q
        pip install torch -q
    fi
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

echo ""
echo "  [ЗАПУСК] PalmPay Terminal..."
echo ""

python main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "  [ОШИБКА] Произошла ошибка"
    echo "  Попробуйте: pip install --upgrade PyQt5 mediapipe"
    read -p "  Нажмите Enter..."
fi
