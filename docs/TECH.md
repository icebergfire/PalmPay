# Техническая документация

## 1. Архитектура

PalmPay остаётся single-page mobile web client в [`../mobile/palmpay.html`](../mobile/palmpay.html), но scan engine теперь построен как passive pipeline.

```text
Camera stream
  -> MediaPipe Hands
  -> Continuous hand tracking
  -> Palm ROI extraction
  -> Quality scoring
  -> Passive liveness / anti-spoof heuristics
  -> Auto frame selection
  -> Feature extraction
  -> Matching
```

## 2. Основные модули

- `Nav`: анимированные переходы между экранами.
- `DB`: локальное хранение профилей и транзакций.
- `Bio`: feature extraction, embedding fusion, calibration и matching.
- `Scan`: камера, tracking, quality scoring, passive liveness и auto-capture.
- `UI`: рендер истории, профилей, badge и toast/modal.
- `A`: ввод суммы.
- `App`: registration / payment orchestration.

## 3. Passive pipeline

### 3.1 Detection и tracking

- MediaPipe Hands работает в непрерывном цикле.
- Landmarks и bbox сглаживаются, чтобы уменьшить jitter.
- Стейт `WAIT` используется только для входа в passive pipeline, без challenge-жестов.

### 3.2 Quality scoring

Каждый ROI оценивается по нескольким метрикам:

- размер ладони в кадре;
- положение относительно центра;
- openness ладони;
- фронтальность;
- освещение;
- contrast;
- sharpness;
- line/edge density;
- glare penalty.

Итоговый `quality score` используется как gate для auto-capture.

### 3.3 Auto frame selection

Приложение не просит пользователя "сканировать" ладонь:

- непрерывно анализирует stream;
- ждёт достаточный `quality score`;
- добирает несколько лучших кадров;
- финальный embedding строит медианой по top candidates.

## 4. Feature extraction

Текущая реализация использует 3 канала.

### 4.1 Geometry

`geo` строится из landmarks:

- нормализованные координаты;
- расстояния между ключевыми точками;
- углы суставов;
- пропорции ладони и пальцев.

### 4.2 Visual

`visual` строится через MobileNetV2 на crop ладони `224x224`.

### 4.3 Texture / palm lines

`texture` строится lightweight-эвристикой на canvas:

- ориентированные edge histogram;
- cell-based energy map;
- line strength в центральной зоне ладони;
- contrast / edge density / glare-aware stats.

Это не специализированная palm-line neural model, но уже лучше чистой геометрии для RGB-only сценария.

## 5. Matching

Matching теперь двухступенчатый:

1. Coarse shortlist по `geo`.
2. Fused score по `visual + texture + geo`.

Веса текущей fusion-модели:

- `visual = 0.40`
- `texture = 0.35`
- `geo = 0.25`

Также есть:

- margin check против ambiguous matches;
- cross-channel agreement check;
- персональный threshold на профиль.

## 6. Passive liveness и anti-spoof

Active gestures удалены. Вместо них используются RGB-эвристики:

- micro-motion landmarks;
- brightness variation во времени;
- bbox scale variation;
- openness variation;
- glare / flatness risk.

Этого достаточно для клиентского passive prototype, но это не финальный fintech-grade anti-spoofing.

## 7. Регистрация и оплата

### Регистрация

- пользователь вводит имя;
- открывается passive camera flow;
- система автоматически собирает несколько лучших кадров;
- сохраняются `geo`, `visual`, `texture`, `threshold`, `token`.

### Оплата

Есть два сценария:

- `quickPay()`: сначала passive identity, затем ввод суммы без повторного сканирования;
- `startPay()`: сначала сумма, затем passive confirmation.

## 8. Данные

### Профиль

```javascript
{
  id: string,
  token: string,
  name: string,
  geo: number[] | null,
  visual: number[] | null,
  texture: number[] | null,
  threshold: number,
  ts: string
}
```

### Транзакция

```javascript
{
  id: string,
  merchant: string,
  amount: number,
  who: string,
  ts: string
}
```

## 9. Производительность

Что уже сделано:

- async загрузка ML-библиотек;
- warm-up MobileNet;
- backend preference order `webgl -> wasm -> cpu`;
- coarse geo shortlist до fused scoring;
- capture только на high-quality passive frames.

Что ещё не сделано:

- Web Worker / OffscreenCanvas pipeline;
- native TFLite / CoreML;
- production latency telemetry;
- real vector index уровня HNSW / FAISS.

## 10. Security status

Что есть сейчас:

- локальная обработка биометрии;
- opaque `token` на профиль;
- нет отправки данных на сервер.

Чего пока нет:

- secure at-rest encryption;
- hardware-backed key storage;
- device attestation;
- backend token vault;
- audit trail и policy engine.

То есть текущая версия честно ближе к strong client-side prototype, а не к финальной fintech production architecture.
