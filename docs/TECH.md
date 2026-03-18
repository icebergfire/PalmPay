# Техническая документация

## Биометрический движок v2

### Архитектура

```
Камера → MediaPipe Hands → 21 landmark
                         ↓
               GeoEmbedding (137-dim)
                         ↓
              ┌──────────┴──────────┐
              │   Fused Score       │  cosine similarity
              │   0.65 × visual     │  weighted average
              │ + 0.35 × geo        │
              └──────────┬──────────┘
                         ↓
Камера → Crop Palm → MobileNetV2 → VisualEmbedding (1280-dim)
```

### Геометрический вектор (137 dims)
- Нормализованные координаты 21 точки (63)
- Попарные расстояния ключевых суставов C(11,2)=55 (55)
- Углы в суставах пальцев (12)
- Соотношения длин пальцев (5)
- Пропорции ладони (2)

### Визуальный вектор (1280 dims)
- MobileNetV2 (ImageNet pretrained), penultimate layer
- Вход: 224×224 кроп области ладони
- L2-нормализован

### Калибровка порога
```python
selfSim = average(cosine(session_i, session_j) for all i≠j)
threshold = clip(selfSim * 0.93, min=0.82, max=0.95)
```

### Multi-angle регистрация
- Сессия 1: ладонь прямо
- Сессия 2: наклон влево ~15°
- Сессия 3: наклон вправо ~15°
- Финальный профиль: медиана всех трёх сессий

### Liveness detection
- Отслеживание вертикального движения кончика указательного пальца
- Порог: отклонение > 4% от базовой линии в 5+ кадрах подряд
- Защита от фото и видеозаписи

---

## База данных (мобильная версия)

### localStorage schema
```javascript
// Профили: ключ 'pp4'
[{
  id: string,        // UTC timestamp base36
  name: string,
  geo: number[],     // 137-dim geometric embedding
  visual: number[],  // 1280-dim visual embedding
  threshold: number, // calibrated threshold (0 = default 0.88)
  ts: ISO8601
}]

// Транзакции: ключ 'pp4_tx'
[{
  id: string,
  merchant: string,
  amount: number,    // рубли
  who: string,       // имя плательщика
  ts: ISO8601
}]
```

---

## API модулей (JS)

### Bio
```javascript
Bio.loadTF()                          // загрузить MobileNet
Bio.geoEmb(landmarks)                 // → float32[] геометрия
Bio.getVisualEmb(video, bbox)         // → float32[] визуал (async)
Bio.medianEmb(embeddings[])           // → медианный вектор
Bio.calibrate(sessions[])             // → порог 0.82-0.95
Bio.identify(visual, geo)             // → {match, score, threshold, name}
Bio.ready                             // boolean
```

### DB
```javascript
DB.add(name, {geo, visual})           // → id
DB.update(id, patch)                  // обновить поля профиля
DB.remove(id)                         // удалить профиль
DB.all()                              // → profiles[]
DB.count()                            // → number
DB.txAdd(merchant, amount, who)       // сохранить транзакцию
DB.txAll()                            // → transactions[]
DB.txClear()                          // очистить историю
```

### Scan
```javascript
Scan.start(mode, callback)            // mode: 'reg'|'pay'
Scan.stop()                           // остановить сканирование
Scan.retry()                          // повтор после ошибки камеры
// callback(result) → {geo, visual, _calibThreshold}
```

### Nav
```javascript
Nav.to(screenId, direction)           // direction: 'fwd'|'back'
// screens: s1, sreg, sscan, s3, s4, s5, s5e, shist, sprof
```

---

## Фазы сканирования

```
INIT → WAIT → CAP → LIVENESS → SCAN → DONE
        ↑________________________|
              (если ладонь убрана)
```

| Фаза | Описание |
|------|----------|
| WAIT | Ожидание ладони в кадре |
| CAP | Захват (flash + вибрация) |
| LIVENESS | Движение пальца (5 кадров) |
| SCAN | Сбор эмбеддингов, прогресс-бар |
| DONE | Передача результата в callback |

---

## Производительность

| Метрика | Значение |
|---------|----------|
| Первая загрузка (с интернетом) | ~15-30 сек (ML модели) |
| Повторный запуск (кеш) | < 2 сек |
| Регистрация (3 сессии) | ~45-60 сек |
| Идентификация | ~5-8 сек |
| Размер приложения | 83 КБ (HTML) |
| ML модели (кеш) | ~19 МБ |
