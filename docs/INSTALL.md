# Инструкция по запуску

## 1. Что нужно

- iPhone c Safari или Android с Chrome.
- Камера.
- Интернет для первой загрузки ML-библиотек.
- HTTPS для реального mobile usage и PWA installation.

## 2. Локальный запуск

Для локальной проверки интерфейса и client logic:

```bash
cd mobile
python3 -m http.server 5504
```

Открывайте:

```text
http://localhost:5504/palmpay.html
```

`localhost` подходит для desktop debugging. Для теста на телефоне через другую сеть нужен `https://`.

## 3. Развёртывание

Публикуется каталог `mobile/` целиком:

```text
palmpay.html
manifest.json
sw.js
```

Пример Nginx:

```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    root /var/www/palmpay/mobile;
    index palmpay.html;

    location / {
        try_files $uri $uri/ /palmpay.html;
    }
}
```

## 4. PWA

Текущая версия:

- использует `manifest.json`;
- регистрирует `sw.js` на `http(s)` runtime;
- кеширует shell и ML-артефакты через service worker.

## 5. Как проверить pipeline

### Регистрация

1. Откройте приложение.
2. Нажмите кнопку регистрации.
3. Введите имя.
4. Держите руку естественно в зоне камеры.
5. Дождитесь auto-capture и сохранения профиля.

### Оплата

Вариант 1:

1. Нажмите "Оплатить ладонью".
2. Дождитесь passive identity.
3. Введите сумму.
4. Подтвердите списание без второго сканирования.

Вариант 2:

1. Введите сумму.
2. Откройте passive confirmation.
3. Держите руку в зоне камеры.
4. Дождитесь auto-capture и matching.

## 6. Что смотреть при отладке

- `quality score`: рука должна быть достаточно крупной, открытой и без сильных бликов.
- `liveness`: в живом видеопотоке должно быть естественное микро-движение.
- `spoof risk`: фото/экран должны давать деградацию passive liveness.
- `matching`: проверяйте margin и threshold в success/error flow.

## 7. Ограничения

- Хранение по-прежнему в `localStorage`.
- При очистке браузерных данных профили и история теряются.
- Без CDN first-run не поднимет visual branch.
- Для production-нормы нужны native secure storage, telemetry и полноценный anti-spoof classifier.
