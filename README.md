<div align="center">

# 🌂 Umbrella

**Платформа управления эндпоинтами для корпоративных сетей**

Централизованный контроль трафика, политики блокировок и удалённое управление  
компьютерами на Windows и Linux — self-hosted, open-source, MIT.

[![Python 3.13](https://img.shields.io/badge/python-3.13-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Go 1.22+](https://img.shields.io/badge/go-1.22+-00ADD8.svg?logo=go&logoColor=white)](https://go.dev/)
[![Vue 3](https://img.shields.io/badge/vue-3.x-4FC08D.svg?logo=vue.js&logoColor=white)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL 16](https://img.shields.io/badge/postgres-16-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)
[![Status: WIP](https://img.shields.io/badge/status-work%20in%20progress-orange.svg)]()

[Идея](#-идея) · [Архитектура](#%EF%B8%8F-архитектура) · [Статус](#-статус) · [Быстрый старт](#-быстрый-старт) · [Разработка](#%EF%B8%8F-разработка) · [Roadmap](#%EF%B8%8F-roadmap)

</div>

---

> ⚠️ **Проект в активной разработке.** Готова инфраструктура и фундамент сервера. Функциональность агентов, политик и админки в работе — см. [Roadmap](#%EF%B8%8F-roadmap).

---

## 🎯 Идея

Umbrella — self-hosted решение для управления парком компьютеров в организации, которое не требует облачных сервисов и не стоит $20/устройство/месяц. Объединяет три задачи в одну платформу:

- 🛡️ **Фильтрация трафика** — блокировка доменов, категорий и портов для отдельных агентов или групп
- 📡 **Удалённое управление** — раздача политик, исполнение команд, сбор телеметрии с эндпоинтов
- 📊 **Прозрачность в реальном времени** — метрики, события и аудит через современную админку

По сути — open-source альтернатива связке Cisco Umbrella + Microsoft Intune, только проще и под твоим контролем.

---

## 🏗️ Архитектура

Umbrella — монорепо из трёх приложений и общих пакетов:

| Компонент | Стек | Назначение |
|-----------|------|------------|
| **Server** | Python 3.13 · FastAPI · SQLAlchemy 2.0 · Dishka · PostgreSQL 16 | Policy engine, координация агентов, приём метрик, API для админки |
| **Web** | Vue 3 · TypeScript · PrimeVue · Pinia · TanStack Query | Админка: управление агентами, политиками, телеметрия |
| **Agent** | Go 1.22+ · gopsutil · Windows Service API | Применение политик на эндпоинте, сбор метрик, исполнение команд |
| **Protocol** | OpenAPI 3.1 | Общая схема API между server и agent, codegen для обеих сторон |

### Принципы проектирования

- **Domain-first структура** — код организован по бизнес-доменам (`agents/`, `policies/`, `commands/`), а не по техническим слоям
- **Чистая ответственность** — репозитории владеют SQL, сервисы — бизнес-логикой, роутеры только мапят HTTP ↔ домен
- **Асинхронность сверху донизу** — `asyncpg`, `httpx`, `AsyncSession`, никаких блокирующих вызовов в event loop
- **Poll, а не push** — агенты сами ходят на сервер, открытые порты на эндпоинтах не нужны
- **mTLS по умолчанию** — каждый агент получает уникальный сертификат с коротким сроком жизни
- **DI через Dishka** — сервисы переиспользуются между HTTP-роутерами и фоновыми задачами

---

## 📍 Статус

### Готово

- ✅ Монорепо-структура с разделением `apps/` и `infra/`
- ✅ PostgreSQL 16 + async SQLAlchemy 2.0 + Alembic
- ✅ Docker-окружение разработки с hot-reload сервера
- ✅ PDM для управления Python-зависимостями
- ✅ Настроенные линтеры (ruff) и конфигурация тестов (pytest + asyncio)
- ✅ `.gitignore` / `.dockerignore` под полный стек
- ✅ Makefile как единая точка входа

### В активной работе

- 🔨 Ядро сервера: конфиг, базовые исключения, DI-контейнер
- 🔨 Первый домен — `agents` (регистрация, heartbeat, список)
- 🔨 Alembic env.py под async SQLAlchemy

### Ещё не начато

- ⏳ Остальные домены (policies, groups, commands, metrics, events)
- ⏳ PKI: выпуск клиентских сертификатов, mTLS middleware
- ⏳ Go-агент
- ⏳ Vue-админка
- ⏳ Prometheus + Grafana integration
- ⏳ Production-деплой (nginx, TLS, бэкапы)

---

## 🚀 Быстрый старт

> Пока работает только поднятие сервера с БД. Админка и агент ещё не готовы.

### Что нужно установить

- Docker 24+ с BuildKit
- `docker compose` v2
- `make`
- Linux или macOS (на Windows — через WSL2)

### Запуск dev-стека

```bash
# Склонировать репо
git clone https://github.com/FlowEcosystem/flow-umbrella.git
cd flow-umbrella

# Скопировать шаблон переменных окружения
cp .env.example .env

# Поднять Postgres + server
make up
```

Первая сборка занимает 2–3 минуты (установка зависимостей), последующие — секунды.

| Сервис | URL | Что там |
|--------|-----|---------|
| Server API | http://localhost:8000 | FastAPI |
| Swagger docs | http://localhost:8000/docs | Автогенерируемая документация API |
| Health-check | http://localhost:8000/health | Простой статус |
| PostgreSQL | `localhost:5432` | `umbrella` / `umbrella` (dev) |

> ⚠️ Дефолтные пароли только для локальной разработки. Перед боевым деплоем — смена всех секретов, настройка TLS, ограничение доступа к БД.

---

## 🛠️ Разработка

### Структура репозитория

```
flow-umbrella/
├── apps/
│   ├── umbrella-server/     # Python API (FastAPI) — в разработке
│   ├── umbrella-web/        # Админка на Vue 3 — пустая заготовка
│   └── umbrella-agent/      # Go-агент — пустая заготовка
├── packages/
│   └── umbrella-protocol/   # Общие схемы API — пустая заготовка
├── infra/
│   └── docker/              # docker-compose файлы
├── docs/                    # Документация
└── Makefile                 # Единая точка входа
```

### Частые команды

| Команда | Что делает |
|---------|------------|
| `make up` | Поднять стек в фоне |
| `make down` | Остановить стек |
| `make restart` | Перезапустить стек |
| `make build` | Пересобрать образы |
| `make rebuild` | Пересобрать с нуля (no-cache) и поднять |
| `make logs` | Смотреть логи сервиса (`s=server` по умолчанию) |
| `make logs-all` | Логи всех сервисов |
| `make ps` | Статус контейнеров |
| `make shell s=server` | Открыть bash внутри контейнера |
| `make db` | Открыть `psql` внутри Postgres |
| `make migrate` | Применить pending-миграции |
| `make migration m="описание"` | Создать новую миграцию через alembic |
| `make clean` | Остановить стек и удалить volumes (с подтверждением) |

### Создание миграции

```bash
# 1. Отредактировать SQLAlchemy-модели в apps/umbrella-server/src/umbrella_server/domains/
# 2. Сгенерировать миграцию
make migration m="add agents table"
# 3. Посмотреть сгенерированный файл в apps/umbrella-server/migrations/versions/
# 4. Применить
make migrate
```

---

## 🗺️ Roadmap

### Этап 1 — фундамент сервера
- [x] Структура монорепо
- [x] Docker-окружение
- [x] pyproject.toml + PDM + lock-файл
- [ ] `core/config.py`, `core/exceptions.py`
- [ ] `db/base.py`, `db/session.py`
- [ ] Dishka-контейнер с providers
- [ ] Alembic под async + первая миграция
- [ ] `/health` endpoint

### Этап 2 — первый домен (agents)
- [ ] SQLAlchemy-модели Agent, AgentGroup
- [ ] Pydantic-схемы
- [ ] AgentRepository + AgentService
- [ ] HTTP-роутеры: register, heartbeat, list, detail
- [ ] Тесты (unit + e2e)

### Этап 3 — PKI и безопасность
- [ ] Bootstrap корневого CA
- [ ] Выпуск клиентских сертификатов при регистрации
- [ ] mTLS middleware для endpoints агентов
- [ ] nginx в compose с TLS termination

### Этап 4 — остальные домены
- [ ] `policies` — правила блокировок
- [ ] `groups` — группы агентов
- [ ] `commands` — очередь команд, long-polling
- [ ] `metrics` — приём и хранение телеметрии
- [ ] `events` — аудит-лог

### Этап 5 — Go-агент
- [ ] Клиент HTTP + mTLS
- [ ] Цикл poll policy / commands / push metrics
- [ ] hosts-file enforcer
- [ ] firewall enforcer (Linux: iptables/nftables)
- [ ] firewall enforcer (Windows: netsh/WFP)
- [ ] Windows Service wrapper
- [ ] MSI-инсталлер (WiX)
- [ ] deb/rpm-пакеты (nfpm)

### Этап 6 — админка
- [ ] Scaffold Vue 3 + PrimeVue + TypeScript
- [ ] Генерация API-клиента из OpenAPI
- [ ] Страница списка агентов
- [ ] Страница деталей агента с графиками метрик
- [ ] Редактор политик
- [ ] Управление группами
- [ ] История команд

### Этап 7 — observability и production
- [ ] Prometheus /metrics на сервере
- [ ] Grafana-дашборды как код
- [ ] structlog + JSON-логи
- [ ] Production-compose с TLS и бэкапами
- [ ] CI (GitHub Actions): lint + test + build

---

## 📖 Документация

Раздел будет наполняться по мере разработки.

| Документ | О чём | Статус |
|----------|-------|--------|
| [`docs/architecture.md`](./docs/architecture.md) | Общий дизайн и взаимодействие компонентов | 📝 планируется |
| [`docs/api.md`](./docs/api.md) | Справочник REST API с примерами | 📝 планируется |
| [`docs/agent-protocol.md`](./docs/agent-protocol.md) | Жизненный цикл агента, mTLS, формат команд | 📝 планируется |
| [`docs/deployment.md`](./docs/deployment.md) | Production-деплой с TLS, бэкапами | 📝 планируется |
| [`docs/security.md`](./docs/security.md) | Модель угроз, PKI, работа с чувствительными данными | 📝 планируется |

---

## 🤝 Контрибьюции

Проект пока в стадии активной разработки одним автором, внешние PR приветствуются, но архитектурные решения могут меняться. Если хочешь помочь:

1. Посмотри [открытые issues](https://github.com/FlowEcosystem/flow-umbrella/issues) — возможно, задача уже в работе
2. Для нетривиальных изменений сначала открой discussion
3. Соблюдай стиль: `ruff` для Python (позже `gofmt` для Go, Prettier для TypeScript)

---

## ⚠️ Ответственное использование

Umbrella даёт организации серьёзную видимость в активность на эндпоинтах. Ответственность за легальное и этичное использование полностью на операторе:

- Предупреди пользователей о мониторинге — это требование GDPR и большинства национальных законов
- Подготовь и опубликуй acceptable-use policy
- Соблюдай региональные законы о персональных данных
- Никогда не разворачивай этот софт на устройствах, которыми ты не владеешь или на которые у тебя нет явного разрешения

Проект создан для легитимного сетевого администрирования. Использование для слежки, вредоносных действий или нарушения приватности третьих лиц не поддерживается.

---

## 📄 Лицензия

MIT License — подробности в [`LICENSE`](./LICENSE).

---

<div align="center">

Построено с любовью к инженерии и неприязнью к enterprise SaaS-ценникам.

[⬆ наверх](#-umbrella)

</div>