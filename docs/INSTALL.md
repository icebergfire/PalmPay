# Инструкция по установке

## Мобильная версия (iOS)

### Требования
- iPhone с iOS 15 и выше
- Safari браузер
- Интернет для первого запуска (~19 МБ для загрузки ML-моделей)

### Установка
1. Передай файл `palmpay.html` на iPhone (Telegram, AirDrop, iCloud)
2. Открой файл в **Safari** (не Chrome, не Firefox)
3. Safari → кнопка «Поделиться» → **«На экран "Домой"»**
4. При первом сканировании разреши доступ к камере

### Права камеры (если не спросил)
```
Настройки → Safari → Камера → Разрешить
```

---

## Мобильная версия (Android)

### Требования
- Android 8+ 
- Chrome браузер

### Установка
1. Передай файл `palmpay.html` на телефон
2. Открой в **Chrome**
3. Меню ⋮ → **«Добавить на главный экран»**
4. Разреши доступ к камере

---

## Развёртывание на веб-сервере (рекомендуется)

Для полноценной работы PWA (Service Worker, офлайн-режим) нужен HTTPS:

```bash
# Nginx конфиг
server {
    listen 443 ssl;
    server_name yourdomain.com;
    root /var/www/palmpay;
    
    location / {
        try_files $uri $uri/ /palmpay.html;
    }
    
    # Важно для Service Worker
    add_header Service-Worker-Allowed "/";
}
```

Скопируй на сервер:
```
palmpay.html
sw.js
manifest.json
```

---

## Десктопная версия

### Windows
```
Двойной клик: run_windows.bat
```

### macOS
```bash
chmod +x run_macos.sh
./run_macos.sh
```

### Linux
```bash
chmod +x run_linux.sh
./run_linux.sh
```

### Ручная установка
```bash
cd desktop/
python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install PyQt5 opencv-python mediapipe numpy
python3 main.py
```

### Проблема с PyQt5 на Mac M1/M2/M3
```bash
pip install PyQt6 opencv-python mediapipe numpy
# Замени во всех файлах ui/: from PyQt5 → from PyQt6
```

---

## Первый запуск

1. **Зарегистрируй ладонь** → «Подключить Palm Pay» → введи имя → сканируй (3 позиции)
2. **Оплата** → введи сумму → поднеси ладонь → подтверди живость
3. **История** → нижняя навигация → «История операций»
4. **Профили** → нижняя навигация → «Профили ладони»
