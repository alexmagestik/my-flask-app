# my-flask-app

Простое Flask-приложение с эндпоинтами для проверки работоспособности, системной информации и арифметических операций. Запускается в Docker, доступно напрямую через порт **5001** и через nginx-интерфейс на порту **8080**.

## Структура проекта

```
.
├── app.py                  # Flask-приложение
├── requirements.txt        # Flask + gunicorn
├── Dockerfile              # Образ my-flask-app (внутренний порт 5000)
├── docker-compose.yml      # flask-app + nginx
├── .dockerignore
├── nginx/
│   ├── default.conf        # reverse proxy /api/* → flask-app:5000
│   └── html/index.html     # демонстрационный веб-интерфейс
└── README.md
```

## Эндпоинты

| Метод | Путь | Описание | Пример |
|-------|------|----------|--------|
| GET | `/` | Список эндпоинтов | `curl localhost:5001/` |
| GET | `/health` | Проверка работоспособности (status, uptime, время) | `curl localhost:5001/health` |
| GET | `/info` | Информация о системе и контейнере | `curl localhost:5001/info` |
| GET | `/multiply/<a>/<b>` | Умножение двух чисел | `curl localhost:5001/multiply/6/7` |
| GET | `/divide/<a>/<b>` | Деление двух чисел | `curl localhost:5001/divide/10/4` |

Примеры ответов:

```json
{"operation": "multiply", "a": 6, "b": 7, "result": 42}
```

```json
{"status": "ok", "uptime_seconds": 12.481, "timestamp": "2026-11-12T10:15:00+00:00"}
```

Ошибки возвращаются в JSON с кодом `400` — например, деление на ноль или нечисловой параметр:

```json
{"error": "Division by zero is not allowed"}
```

## Быстрый старт (Docker Compose)

Требуется установленный Docker Desktop / Docker Engine с плагином Compose.

```bash
# Собрать образы и запустить контейнеры в фоне
docker compose up -d --build

# Проверить статус
docker compose ps

# Смотреть логи
docker compose logs -f
```

После запуска:

* **Flask напрямую:** http://localhost:5001
* **nginx-интерфейс:** http://localhost:8080
* **Health через nginx:** http://localhost:8080/health

Остановка и удаление:

```bash
docker compose down          # остановить и удалить контейнеры
docker compose down --rmi local   # дополнительно удалить собранный образ
```

## Проверка через curl

```bash
curl http://localhost:5001/health
curl http://localhost:5001/info
curl http://localhost:5001/multiply/6/7
curl http://localhost:5001/divide/10/4

# Те же запросы через nginx (префикс /api)
curl http://localhost:8080/api/health
curl http://localhost:8080/api/multiply/6/7
```

Ожидаемый результат:

```text
$ curl -s http://localhost:5001/multiply/6/7
{"a":6,"b":7,"operation":"multiply","result":42}
```

## Сборка и запуск только Flask-образа

```bash
# Сборка
docker build -t my-flask-app .

# Запуск: host 5001 → container 5000
docker run -d --name my-flask-app -p 5001:5000 my-flask-app

# Проверка
curl http://localhost:5001/health

# Остановка
docker stop my-flask-app && docker rm my-flask-app
```

`Dockerfile` использует `python:3.12-slim`, устанавливает зависимости из `requirements.txt`, запускает приложение от непривилегированного пользователя через **gunicorn** (2 воркера) на порту `5000` и содержит `HEALTHCHECK`.

## Как работает nginx

`nginx/default.conf`:

* отдаёт статическую страницу `nginx/html/index.html` на `/`;
* проксирует `/api/*` в `http://flask-app:5000/*`, убирая префикс `/api`
  (например, `/api/multiply/6/7` → `/multiply/6/7`);
* проксирует `/health` в Flask для внешних проверок.

Демо-страница на http://localhost:8080 позволяет ввести числа и выполнить умножение/деление, а также запросить `health` и `info` — результат отображается в панели «Ответ».

## Локальный запуск без Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py            # http://localhost:5000
```

Или через gunicorn:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 app:app
```

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|------------|--------------|------------|
| `PORT` | `5000` | Внутренний порт, который слушает gunicorn |

## Устранение неполадок

| Проблема | Решение |
|----------|---------|
| `port is already allocated` | Порт 5001 или 8080 занят — измените маппинг в `docker-compose.yml` или остановите конфликтующий контейнер |
| nginx отвечает `502 Bad Gateway` | Flask-контейнер ещё не готов или упал: `docker compose logs flask-app`, `docker compose ps` |
| Изменения в `app.py` не применяются | Образ нужно пересобрать: `docker compose up -d --build` |
| Нужно зайти внутрь контейнера | `docker compose exec flask-app sh` |
