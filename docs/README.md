# PalmPay

PalmPay теперь работает как mobile-first система пассивного распознавания ладони через камеру смартфона. Пользователь не выполняет liveness-жесты и не проходит отдельное "сканирование": приложение анализирует видеопоток, само оценивает качество кадров, само выбирает лучшие фреймы и затем выполняет matching.

## Что реально есть в текущем коде

- Непрерывный video stream через `getUserMedia`.
- Continuous hand detection и tracking на MediaPipe Hands.
- Passive liveness без команд пользователю.
- Quality scoring по резкости, освещению, положению ладони, фронтальности и glare.
- Auto frame selection и auto-capture лучших кадров.
- 3-канальная биометрия:
  - `visual` через MobileNetV2,
  - `texture` по palm lines / edge / skin texture heuristics,
  - `geo` по landmarks.
- Multi-stage matching: coarse shortlist по геометрии + fused score.
- PWA runtime: `manifest.json` + `sw.js`.

## Структура проекта

```text
PalmPay/
├── mobile/
│   ├── palmpay.html      # основной UI, CV pipeline и matching
│   ├── manifest.json     # PWA manifest
│   └── sw.js             # service worker и offline cache
└── docs/
    ├── README.md         # обзор
    ├── TECH.md           # архитектура и pipeline
    ├── INSTALL.md        # запуск и деплой
    ├── AUDIT.md          # аудит и remove/replace matrix
    └── ROADMAP.md        # план развития
```

## Технологический стек

| Область | Технология |
|--------|------------|
| UI | HTML5, CSS3, vanilla JavaScript |
| Hand tracking | MediaPipe Hands |
| Visual embedding | TensorFlow.js + MobileNetV2 |
| Texture features | lightweight canvas-based edge / line / texture extraction |
| Storage | `localStorage` |
| Runtime APIs | Camera, Vibration, Service Worker |
| Packaging | PWA |

## Ограничения текущей версии

- Это по-прежнему browser-only клиент без нативного Secure Enclave / Keychain / Keystore.
- Профили и история транзакций живут локально в браузере на одном устройстве.
- Matching рассчитан на небольшой on-device профильный набор; полноценный vector index уровня FAISS/HNSW пока не внедрён.
- Passive anti-spoofing основан на RGB-эвристиках и не равен нативному fintech-grade сенсору.
- ML-библиотеки грузятся с CDN при старте, поэтому первая загрузка требует сеть.

## Карта документации

- [`TECH.md`](TECH.md): обновлённая архитектура passive pipeline, feature extraction, liveness, matching, security status.
- [`INSTALL.md`](INSTALL.md): запуск локально, PWA deployment, mobile usage и проверка pipeline.
- [`AUDIT.md`](AUDIT.md): проблемы, что удалено/заменено и как безопасно интегрировать дальнейшие изменения.
- [`ROADMAP.md`](ROADMAP.md): быстрые, средние и продвинутые этапы развития.
