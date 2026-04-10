# Аудит PalmPay

## Критические проблемы, найденные до рефакторинга

1. Активный scan-flow противоречил целевой UX-модели: пользователь должен был выполнять отдельные liveness-действия.
2. `quickPay()` фактически делал два сканирования: один для идентификации, второй для подтверждения.
3. `manifest.json`, runtime manifest и `sw.js` ссылались на разные entrypoint-файлы.
4. В UI было обещание про шифрование, которого в коде не было.
5. Matching был линейным и двухканальным, без texture-based palm features.
6. Регистрация была завязана на активный multi-angle сценарий, который плохо сочетается с passive capture.

## Что удалено / заменено

| Тип | Что было | Что стало | Почему |
|-----|----------|-----------|--------|
| `remove` | gesture-based liveness prompts | passive liveness по temporal heuristics | active UX ломал целевую модель |
| `remove` | multi-angle registration UI | passive multi-frame capture | старая логика требовала специальных действий |
| `replace` | 2-channel matching (`visual + geo`) | 3-channel matching (`visual + texture + geo`) | нужна устойчивость к RGB-ограничениям |
| `replace` | linear full-scan matching | coarse geo shortlist + fused score | быстрее и стабильнее на мобильном |
| `replace` | повторное сканирование после `quickPay()` | reuse уже найденной identity | уменьшение latency и friction |
| `replace` | inconsistent PWA entrypoint | единый `palmpay.html` | исправление runtime ошибок |
| `replace` | misleading encryption copy | честный local-processing copy | безопасность должна соответствовать реальности |

## Что ещё остаётся слабым местом

- Нет защищённого хранения embedding на уровне OS secure storage.
- Нет device binding и server-side risk engine.
- Нет production telemetry по FAR/FRR, latency и spoof false positives.
- Нет нативного inference path через CoreML / TFLite.

## Безопасная стратегия дальнейшей интеграции

1. Сохранять внешний API `Scan.start/stop/retry`, чтобы не ломать UI.
2. Добавлять новые фичи через quality/liveness/matching слои, а не переписывать весь экран.
3. Любое усиление security делать только после выноса хранения из `localStorage`.
4. Native optimization внедрять отдельным слоем, не смешивая её с UI-рефакторингом.
