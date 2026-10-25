# Shorts Clipper (бесплатно / offline)

Нарезка длинного видео в вертикальные Shorts (9:16) **без платных сервисов**.  
Детект моментов — по энергии звука (FFmpeg + Python). Баннер букмекера/сайта — опционально.

Нужен только **FFmpeg** / **ffprobe** в `PATH`.

## Быстрый старт

```bash
# 1) Найти моменты
python3 -m shorts_clipper detect long.mp4 --count 8 --duration 30 --out moments.json

# 2) Нарезать Shorts
python3 -m shorts_clipper cut long.mp4 --out clips/ --moments moments.json

# Или всё сразу (авто-детект + cut)
python3 -m shorts_clipper cut long.mp4 --out clips/ --count 5 --duration 25

# Позже — с баннером внизу кадра
python3 -m shorts_clipper cut long.mp4 --out clips/ --moments moments.json --banner banner.png
```

## Ручные таймкоды

```bash
python3 -m shorts_clipper cut long.mp4 --out clips/ --timestamps 1:00-1:30,5:10-5:45,12:00
```

Голый таймкод (`12:00`) = клип длиной `--duration` начиная с этой секунды.

## Полезные флаги

| Флаг | Зачем |
|------|--------|
| `--dry-run` | Показать план и ffmpeg-команды без рендера |
| `--save-moments path.json` | Сохранить выбранные моменты |
| `--banner-height 0.12` | Высота баннера (доля кадра) |
| `--prefix promo` | Префикс имён файлов |

```bash
python3 -m shorts_clipper cut --help
python3 -m shorts_clipper info long.mp4
```

## Типичный workflow под рекламу

1. Растишь канал **без баннера** (`cut` без `--banner`).
2. Когда есть охваты — те же `moments.json` + `--banner banner.png`.
3. Моменты можно поправить руками в JSON или через ChatGPT по транскрипту, затем `--moments`.

## Ограничения

- Энергия звука ≠ идеальный «вирусный» хук: после детекта лучше глянуть 8–10 кандидатов и отбросить слабые.
- Для речи точнее связка Whisper → LLM → `--moments` / `--timestamps` (не входит в минимальный free-стек, но JSON тот же).
- Реклама беттинга: маркировка и правила YouTube/закона — на вашей стороне.
