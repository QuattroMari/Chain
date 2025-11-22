# Video Analysis Service

Микросервис для анализа видео на наличие движения в кадре. Использует OpenCV для детекции движения и сохраняет результаты в PostgreSQL.

Нужны Docker и Docker Compose

Запуск:
```
docker-compose up --build
```

Сервис будет доступен по адресу: `http://localhost:8000`

Эндпоинты:

# POST /analyze

Анализирует загруженное видео на наличие движения

**Request**
```
curl -X POST "http://localhost:8000/analyze" \ -F "file=@video.mp4"
```

**Response (JSON)**
```
{
  "id": 1,
  "filename": "video.mp4",
  "has_motion": true,
  "motion_score": 45.7,
  "processing_time": 12.34,
  "status": "completed",
  "created_at": "2024-01-15T14:30:25.123456"
}
```
**Форматы:** `.mp4`, `.avi`, `.mov`, `.mkv`, `.flv`, `.wmv`  
**Макс. размер файла:** 500 MB

# GET /metrics

Возвращает метрики в формате Prometheus

**Request**
curl http://localhost:8000/metrics


**Response** Метрики в формате Prometheus:
**Метрики**
- `video_analysis_total` - общее кол-во обработанных видео
- `video_analysis_processing_time_seconds` - время обработки (гистограмма)
- `video_analysis_errors_total` - кол-во ошибок
- `video_analysis_motion_detected_total` - кол-во видео с движением

### GET /docs

Документация API: `http://localhost:8000/docs`


## Стек:

- **Python 3.11+**
- **FastAPI** - веб-фреймворк
- **PostgreSQL** - база данных
- **OpenCV** - анализ видео
- **SQLAlchemy** - ORM
- **Prometheus** - метрики
- **Docker** - контейнеризация



