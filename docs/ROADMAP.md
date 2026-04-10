# Roadmap

## Быстрые улучшения (1–3 дня)

- Вынести quality thresholds и matching weights в отдельный config-блок.
- Добавить debug overlay для quality / liveness / spoof score.
- Ограничить размер базы профилей и ввести health-check для degraded matching.
- Очистить остаточный dead code и web-only metadata.

## Средние улучшения (1–2 недели)

- Перевести хранение профилей из `localStorage` в защищённый storage-слой.
- Добавить coarse-to-fine vector index для большего числа профилей.
- Улучшить palm ROI normalization и segmentation.
- Добавить calibration dataset и offline evaluation для FAR / FRR / EER.
- Вынести heavy CV logic из одного HTML-файла в отдельные JS-модули.

## Продвинутые улучшения (1–2 месяца)

- Нативный inference path: TFLite / CoreML через wrapper или native shell.
- Device binding, secure enclave backed keys и server-side token vault.
- ML-based spoof classifier по temporal RGB sequence.
- Domain-specific palm embedding вместо общего MobileNet backbone.
- Remote feature revocation, audit logs и risk-based payment policy.
