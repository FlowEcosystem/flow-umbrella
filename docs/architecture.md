# Umbrella — Архитектура

Last updated: 2026-04-25
Status: Draft v4

## Обзор

Umbrella — self-hosted платформа управления endpoint'ами, развёрнутая в нескольких физических локациях (филиалах) одной организации. Делает три вещи:

1. Централизованная фильтрация трафика на endpoint'ах (блокировки на уровне DNS/URL/IP).
2. Удалённое управление endpoint'ами (раздача политик, команды, телеметрия).
3. Агрегация и контроль по всем филиалам из центрального офиса (HQ).

Целевой масштаб: 180+ филиалов, 100–500 endpoint'ов на филиал (~35 000 endpoint'ов суммарно).

Umbrella позиционируется как self-hosted альтернатива Cisco Umbrella + Microsoft Intune, заточенная под организации с распределёнными физическими локациями, которым нужна автономия на каждой точке при единой оркестрации сверху.

---

## Топология

Umbrella — **федеративная, не multi-tenant.** Каждый филиал запускает свой автономный стек. HQ — отдельный сервис поверх всех филиалов, агрегирует данные. Филиалы не делят между собой инфраструктуру, и HQ не является точкой отказа для работы филиала.

```
                    ┌────────────────────────┐
                    │   HQ Server            │
                    │   hq.umbrella.su       │
                    │   (публичный IP)       │
                    │                        │
                    │   - глобальные политики│
                    │   - агрегированные     │
                    │     метрики            │
                    │   - реестр филиалов    │
                    │   - оркестровка        │
                    │     rollout'ов         │
                    └────────────▲───────────┘
                                 │
                   исходящие HTTPS от филиалов
                   (heartbeat, события, pull)
                                 │
      ┌──────────────┬───────────┼───────────┬──────────────┐
      │              │           │           │              │
┌─────┴────┐   ┌─────┴────┐  ...больше... ┌──┴───────┐  ┌───┴──────┐
│ Филиал 1 │   │ Филиал 2 │               │ Филиал N │  │Филиал 180│
│ (Казань) │   │ (СПб)    │               │          │  │          │
│          │   │          │               │          │  │          │
│ umbrella-server + локальная БД + админка │         │  │          │
│    ▲           ▲                         │         │  │          │
│    │ mTLS      │ mTLS                    │         │  │          │
│    │           │                         │         │  │          │
│ spider      agents (~100–500 хостов)     │         │  │          │
│ (роутер)                                 │         │  │          │
└──────────┘   └──────────┘                └─────────┘  └──────────┘
```

**Правила коннектов:**

- Филиалы инициируют весь исходящий трафик в HQ. HQ никогда не ходит в филиалы сам. Филиалы за NAT/файерволом, без публичных IP.
- Агенты и spider'ы подключаются только к локальному серверу своего филиала, никогда напрямую к HQ.
- HQ имеет статический публичный домен (`hq.umbrella.su`) и TLS-сертификат.
- У каждого филиала свой домен/DNS (например, `kazan.umbrella.su` или только локальный адрес).

**Автономность:**

- Если HQ недоступен — филиалы продолжают работать. Агенты опрашивают локальный сервер филиала, политики применяются, телеметрия собирается.
- Простой HQ отображается в админке филиала как предупреждение, не как блокер.
- Когда HQ возвращается — филиалы досылают накопившиеся события и подтягивают версии политик.

---

## Компоненты

### umbrella-server (филиал)

Python 3.13 / FastAPI / SQLAlchemy async / PostgreSQL 16. Упакован в Docker Compose-стек. По одному инстансу на филиал, по одной PostgreSQL-базе на филиал. Между филиалами нет общего хранилища.

**Стек:**
- FastAPI 0.115+, uvicorn, pydantic v2 + pydantic-settings
- SQLAlchemy 2.0 async + asyncpg
- Alembic (миграции)
- Dishka (async DI-контейнер)
- structlog (JSON-логи), prometheus-client
- python-jose (JWT), bcrypt, cryptography (PKI)
- Менеджер пакетов: PDM

Отвечает за:
- Админку для локального IT-персонала филиала.
- Enrollment агентов, heartbeat, раздачу политик, диспатч команд, сбор метрик.
- Зеркалирование глобальных политик из HQ; владеет локальными политиками.
- Периодическую исходящую синхронизацию с HQ (heartbeat, агрегированные метрики, критичные события, pull версий политик).

### umbrella-web (фронтенд)

SPA на **Vue 3 / Vite 8 / Tailwind CSS v4** (директория `apps/umbrella-web`, package name `umbrella-web1`). Компонентная система на базе **shadcn-vue** (reka-ui). Ходит в API сервера филиала через axios. Один build-артефакт используется всеми филиалами.

**Стек:**
- Vue 3.5, vue-router 4, Pinia 3
- Tailwind CSS v4 + tailwind-merge + class-variance-authority
- reka-ui (headless-примитивы), lucide-vue-next + @remixicon/vue
- @tanstack/vue-table (таблицы), @vueuse/core (утилиты)
- unplugin-auto-import + unplugin-vue-components (авто-импорты)

**Страницы:** Dashboard, Agents (список + детальная), Groups (список + детальная), Policies (три вкладки: Трафик / Процессы / Сервисы), Admins, Settings, Login.

**Структура фронтенда:**
```
src/
  app/           — роутер, layouts (Default/Empty), http-клиент
  domains/       — feature-домены (auth, agents, groups, policies, admins, dashboard, settings)
    <domain>/
      api.js     — вызовы API
      store.js   — Pinia-стор
      use*.js    — composables страниц
      ui/
        pages/   — страницы
        components/ — диалоги, карточки, вкладки
  shared/
    composables/ — usePagination, usePermissions, usePolling, useSessionExpired, useToast
    ui/          — компоненты-примитивы (Badge, Button, Card, Dialog, Input, Sheet, Table, Tooltip и др.)
    lib/utils.js — cn() и утилиты
```

**Ключевые компоненты по доменам:**
- `agents/` — AgentCreateDialog, AgentEditDialog, AgentTokenDialog, AgentCommandDialog (отправка команды агенту), AgentBulkBar (bulk-операции); useBulkAgents
- `policies/` — PolicyFormDialog, ProcessPolicyFormDialog, PolicyAssignDialog (назначение на группы/агентов), PolicyTestDialog, CsvImportDialog, ServicesTab, ProcessesTab; servicePresets.js (преднастроенные сервисы)
- `groups/` — GroupFormDialog, GroupMembersDialog
- `admins/` — AdminFormDialog

### umbrella-agent

Сервис на Go, ставится на Windows endpoint'ы (первая очередь), позже Linux/macOS. Windows-инсталлер — подписанный MSI; пакетирование для Linux через nfpm (deb/rpm).

**Стек:** Go 1.23+, `golang.org/x/term`, стандартная библиотека. Без внешних зависимостей в рантайме — единый статический бинарник.

**Реализовано:**

- mTLS-аутентификация против локального сервера филиала через клиентский сертификат, выпущенный при enrollment.
- Периодический опрос: политики (~60с), очередь команд (~15с), heartbeat (~30с).
- Исполнение whitelisted-команд (`reboot`, `collect_diagnostics`, `update_self`, `apply_config`).
- Ротация сертификата за `cert_renew_before_days` дней до истечения.
- Управление как системной службой: Windows SCM / systemd.

**TUI (интерактивный режим):**

Запускается при `umbrella-agent` без подкоманды в терминале. Реализован полностью в raw-mode — без переключения в cooked-mode и без внешних зависимостей.

Startup flow при первом запуске:
```
Welcome screen (ASCII-щит, 2с авто-пропуск)
  ↓
Guided wizard (3 шага, всё в raw TUI):
  Шаг 1/3: Server URL          — поле ввода с предзаполнением
  Шаг 2/3: Enrollment Token    — маскированный ввод
  Шаг 3/3: Skip TLS?           — y/N
  → Enrollment (spinner, обработка ошибок с retry)
  ↓
Verify screen (4 последовательных check'а с прогрессивной отрисовкой):
  ✓/✗ Сервер доступен      — GET /health, latency
  ✓/✗ Режим авторизации    — mTLS / Bearer
  ✓/✗ Heartbeat            — POST /v1/agent/heartbeat
  ✓/✗ Получение команд     — GET /v1/agent/commands
  [r] retry  [q] quit  [Enter] continue
  ↓
Install as service (обязательный финальный шаг, показывает итоговый конфиг)
  ↓
Главное меню
```

При возврате (агент уже зарегистрирован): welcome → verify → меню (служба уже запущена) или предложение установить.

Главное меню:
```
1. Настроить агент   — re-enrollment через cooked wizard + установка службы
2. Запустить/остановить службу
3. Мониторинг        — live dashboard, auto-refresh 3s
4. Логи              — journalctl (Linux, auto-refresh 2s) / Event Viewer hint (Windows)
5. Отладка           — конфиг, состояние агента, тест соединения
6. Удалить агент
```

**PKI / TLS:**

Агент при `SetClientCert` строит пул доверия из системных root CA + Branch CA. Это позволяет работать с серверами на Let's Encrypt (система доверяет) и с серверами на приватном Branch CA (явно добавлен в пул) одновременно. `insecure_skip_verify` оставлен как крайний fallback для dev-окружений.

### umbrella-spider

Сервис на Go, ставится на Linux-шлюзы. Целевая платформа: Linux-роутер (Debian/Ubuntu), возможно OpenWrt позже. Mikrotik RouterOS не целевой — Go-бинари на нём нативно не запускаются.

Отвечает за:
- Enforcement на уровне сети через nftables/iptables или dnsmasq.
- Прозрачную фильтрацию для хостов за роутером (покрывает устройства без агентов — гостевые сети, BYOD).
- Тот же sync-протокол, что у агентов: опрос сервера филиала за правилами, push статистики трафика.

### umbrella-hq (в будущем)

Python/FastAPI-сервис, отдельный от сервера филиала. Переиспользует общий код (core, db, DI, capability-система) через shared-пакет в монорепе.

Отвечает за:
- Реестр филиалов: список, статус здоровья, количество агентов.
- Создание глобальных политик: политики, применяемые ко всем или выбранным филиалам.
- Агрегированные дашборды и отчёты.
- Оркестровку rollout'ов: раздача команд "обновитесь до версии X" филиалам пакетами.
- HQ-админов (отдельно от локальных админов филиалов).

---

## Аутентификация и авторизация

Три независимых auth-контекста, никогда не смешиваются:

### Локальные админы филиала

- Учётка: email + пароль, хранится в БД филиала.
- Токены: JWT access (60 мин) + случайный refresh (14 дней) в httpOnly-cookie.
- Роли: `superadmin`, `admin`, `viewer`. Мапятся в capabilities через статическую таблицу (`domains/auth/capabilities.py`).
- Скоуп: только тот филиал, где админ был создан. Никакого кросс-филиального доступа.

**Capability-таблица (текущая):**

| Capability | superadmin | admin | viewer |
|---|---|---|---|
| `self:read`, `self:update` | ✓ | ✓ | ✓ |
| `admins:read`, `admins:write` | ✓ | | |
| `instance:read` | ✓ | ✓ | ✓ |
| `instance:write` | ✓ | | |
| `agents:read` | ✓ | ✓ | ✓ |
| `agents:write` | ✓ | ✓ | |
| `groups:read` | ✓ | ✓ | ✓ |
| `groups:write` | ✓ | ✓ | |
| `policies:read` | ✓ | ✓ | ✓ |
| `policies:write` | ✓ | ✓ | |
| `commands:read` | ✓ | ✓ | ✓ |
| `commands:write` | ✓ | ✓ | |

### Агенты

- Учётка: mTLS клиентский сертификат, выпущенный внутренним Branch CA при enrollment'е.
- Enrollment: одноразовый токен, сгенеренный админом филиала. Агент локально генерирует RSA-ключ и отправляет CSR; сервер подписывает. Токен — single-use, обнуляется после enrollment.
- Ротация сертификата: TTL 30 дней, агент обновляет за `cert_renew_before_days` дней до истечения.
- Nginx проверяет клиентский сертификат (`ssl_client_certificate = ca.crt`, `ssl_verify_client on`), пробрасывает `X-Agent-Cert-CN` (Subject DN RFC 2253) и `X-Agent-Cert-Verified` в FastAPI. FastAPI читает заголовки, извлекает UUID агента из CN (формат `agent:<UUID>`, пример: `CN=agent:550e8400-...`), аутентифицирует по `agent_id`.
- Dev-fallback (без nginx, `AGENT_MTLS=false`): Bearer-токен, проверяется по `agent_token_hash` в таблице `agents`. Выдаётся при enrollment в поле `agent_token`.
- На prod-порту 443 (Admin API) nginx явно зачищает `X-Agent-Cert-CN` через `proxy_set_header`, исключая подделку заголовка.
- Скомпрометированный агент: сертификат отзывается через CRL; агент больше не подключится.

### HQ-админы (в будущем)

- Отдельная таблица пользователей в БД HQ. Никакого общего идентити с админами филиалов.
- Возможность добавить SSO (Microsoft 365, Google Workspace) позже.

### Филиал ↔ HQ

- Каждый филиал разово регистрируется в HQ, получает long-lived access token.
- Токен хранится на сервере филиала, используется для всех запросов к HQ.
- Ротация — ручная (пересоздать токен в HQ-админке → обновить конфиг филиала).

---

## PKI

### Branch CA

При первом старте сервера автоматически генерируется Branch CA (`BranchCA.ensure()`):
- Сертификат: `pki/ca.crt` (10 лет)
- Приватный ключ: `pki/ca.key` (права 600)

Branch CA используется для двух целей:
1. **Подпись клиентских сертификатов агентов** (`sign_csr()`) — при enrollment, TTL 30 дней, EKU=CLIENT_AUTH.
2. **Подпись TLS-сертификата nginx** (`sign_server_cert()`) — генерируется один раз через `make gen-nginx-cert h=hostname`, TTL 1 год, EKU=SERVER_AUTH, SAN=DNS:hostname.

### TLS на порту 8443 (Agent API)

```
Агент                          Nginx :8443                    FastAPI :9090
  │                               │                               │
  │──── TLS ClientHello ─────────>│                               │
  │<─── TLS ServerHello ──────────│  (server.crt, подписан CA)    │
  │     (верифицирует по          │                               │
  │      system roots + Branch CA)│                               │
  │──── Client Certificate ──────>│  (agent.crt, подписан CA)     │
  │                               │──── proxy_pass ──────────────>│
  │                               │     X-Agent-Cert-CN: CN=...   │
  │                               │     X-Agent-Cert-Verified: SUCCESS
```

Почему два корня доверия на агенте:
- Сервер использует Let's Encrypt (публичный CA) → нужны системные root CAs.
- При локальном деплое (без публичного домена) сервер использует сертификат от Branch CA → нужен Branch CA в пуле.
- Агент объединяет оба: `SystemCertPool() + AppendCertsFromPEM(ca_cert_pem)`.

### Генерация nginx-сертификата

```bash
# Из директории apps/umbrella-server
python scripts/gen_nginx_cert.py api.umbrella.su
# Создаёт pki/server.crt и pki/server.key

# Или через Make (если запущен Docker):
make gen-nginx-cert h=api.umbrella.su
```

Nginx конфиг для Agent API (порт 8443):
```nginx
ssl_certificate     /path/to/pki/server.crt;
ssl_certificate_key /path/to/pki/server.key;
ssl_client_certificate /path/to/pki/ca.crt;
ssl_verify_client optional;          # optional: enrollment не требует cert
ssl_verify_depth 1;

location = /v1/agent/enroll {
    # Без проверки cert — токен в теле
    proxy_set_header X-Agent-Cert-CN       "";
    proxy_set_header X-Agent-Cert-Verified "";
    ...
}
location /v1/agent/ {
    if ($ssl_client_verify != "SUCCESS") { return 401; }
    proxy_set_header X-Agent-Cert-CN       $ssl_client_s_dn;
    proxy_set_header X-Agent-Cert-Verified $ssl_client_verify;
    proxy_set_header X-Agent-Cert-Serial   $ssl_client_serial;
    ...
}
```

---

## База данных

### Таблицы (текущие)

| Таблица | Домен | Описание |
|---|---|---|
| `admins` | auth | Локальные администраторы филиала |
| `refresh_tokens` | auth | Refresh-токены сессий |
| `branch_config` | instance | Конфигурация инстанса (одна строка) |
| `agents` | agents | Зарегистрированные endpoint'ы |
| `groups` | groups | Группы агентов |
| `agent_group_memberships` | groups | M2M: agent ↔ group |
| `policies` | policies | Политики фильтрации |
| `services` | policies | Именованные сервисы (наборы правил) |
| `policy_services` | policies | M2M: policy ↔ service |
| `policy_group_assignments` | policies | M2M: policy ↔ group (с assigned_at, assigned_by_id) |
| `policy_agent_assignments` | policies | M2M: policy ↔ agent (с assigned_at, assigned_by_id) |
| `commands` | commands | Команды, отправленные агентам |

### Модели

**Admin** — `email`, `password_hash`, `full_name`, `role` (superadmin/admin/viewer), `is_active`, `last_login_at`, `avatar_url`. Unique-индекс по `email` только среди активных (soft-delete).

**Agent** — `hostname`, `os` (windows/linux/macos), `os_version`, `agent_version`, `ip_address`, `status` (pending/active/disabled/decommissioned), `enrollment_token_hash`, `enrollment_token_expires_at`, `agent_token_hash`, `cert_serial`, `cert_expires_at`, `notes`, `last_seen_at`, `enrolled_at`.

**Group** — `name` (unique среди активных), `description`, `color`. Связь с агентами через `agent_group_memberships`.

**Policy** — `name`, `description`, `kind` (traffic/process), `source` (local/global), `action` (block/allow), `is_active`, `is_global` (bool — флаг глобальной политики), `overridable` (bool), `version` (int), `hq_policy_id` (UUID, nullable), `custom_rules` (JSONB — список правил вида `{type, value}`). Связь с сервисами через `policy_services`, с группами через `policy_group_assignments`, с агентами через `policy_agent_assignments`.

**Service** — `name`, `category`, `description`, `kind` (traffic/process), `source` (local/global), `is_active`, `rules` (JSONB — список `{type, value}`). Именованная группа правил, переиспользуемая в нескольких политиках одного вида.

**Command** — `agent_id` (FK), `issued_by_id` (FK admin, nullable), `type` (reboot/collect_diagnostics/update_self/apply_config), `status` (pending/sent/acknowledged/success/failure/timeout), `payload` (JSON, nullable), `result` (JSON, nullable), `error_message`, `sent_at`, `acknowledged_at`, `completed_at`, `expires_at`.

**PolicyKind** — enum: `traffic` | `process`.

**PolicyRuleType** — enum: `domain`, `url`, `ip`, `process`.

Все основные модели наследуют `UUIDPrimaryKeyMixin`, `TimestampMixin` (created_at, updated_at), `SoftDeleteMixin` (deleted_at).

---

## API endpoints (текущие)

Все endpoint'ы под префиксом `/v1/`. Авторизация — JWT Bearer + capability-check.

### Auth `/v1/auth`
- `POST /v1/auth/login` — получить access + refresh
- `POST /v1/auth/refresh` — обновить access по refresh-cookie
- `POST /v1/auth/logout` — отозвать refresh-токен
- `GET /v1/auth/me` — текущий пользователь

### Admins `/v1/admins`
- `GET /v1/admins` — список (`admins:read`)
- `POST /v1/admins` — создать (`admins:write`)
- `GET /v1/admins/{id}` — детали (`admins:read`)
- `PATCH /v1/admins/{id}` — обновить (`admins:write`)
- `DELETE /v1/admins/{id}` — удалить (`admins:write`)

### Instance `/v1/instance`
- `GET /v1/instance` — конфиг инстанса (`instance:read`)
- `PATCH /v1/instance` — обновить (`instance:write`)

### Agents `/v1/agents`
- `GET /v1/agents` — список с фильтрами (status, os, search) и пагинацией (`agents:read`)
- `POST /v1/agents` — создать + enrollment token (`agents:write`)
- `GET /v1/agents/{id}` — детали (`agents:read`)
- `PATCH /v1/agents/{id}` — обновить (`agents:write`)
- `DELETE /v1/agents/{id}` — удалить (`agents:write`)
- `GET /v1/agents/{id}/groups` — группы агента (`agents:read`)
- `POST /v1/agents/{id}/regenerate-enrollment-token` — пересоздать токен (`agents:write`)

### Groups `/v1/groups`
- `GET /v1/groups` — список с пагинацией (`groups:read`)
- `POST /v1/groups` — создать (`groups:write`)
- `GET /v1/groups/{id}` — детали + счётчик агентов (`groups:read`)
- `PATCH /v1/groups/{id}` — обновить (`groups:write`)
- `DELETE /v1/groups/{id}` — удалить + очистить memberships (`groups:write`)
- `GET /v1/groups/{id}/agents` — агенты группы (`groups:read`)
- `POST /v1/groups/{id}/agents` — добавить агентов (batch) (`groups:write`)
- `DELETE /v1/groups/{id}/agents/{agent_id}` — убрать агента (`groups:write`)

### Policies `/v1/policies`
- `GET /v1/policies` — список с фильтрами (source, action, is_active, kind) и пагинацией (`policies:read`)
- `POST /v1/policies` — создать (`policies:write`)
- `GET /v1/policies/{id}` — детали (`policies:read`)
- `PATCH /v1/policies/{id}` — обновить (`policies:write`)
- `DELETE /v1/policies/{id}` — soft-delete (`policies:write`)

### Services `/v1/services`
- `GET /v1/services` — список с фильтрами (source, category, kind) и пагинацией (`policies:read`)
- `POST /v1/services` — создать (`policies:write`)
- `GET /v1/services/{id}` — детали (`policies:read`)
- `PATCH /v1/services/{id}` — обновить (`policies:write`)
- `DELETE /v1/services/{id}` — soft-delete (`policies:write`)

### Commands `/v1/agents/{agent_id}/commands`
- `POST /v1/agents/{agent_id}/commands` — выдать команду агенту (`commands:write`)
- `GET /v1/agents/{agent_id}/commands` — список команд агента (`commands:read`)
- `GET /v1/agents/{agent_id}/commands/{command_id}` — детали команды (`commands:read`)

### Agent API `/v1/agent` (только через nginx :8443, mTLS)
- `POST /v1/agent/enroll` — enrollment (enrollment_token + CSR в теле, без cert). Ответ: `agent_id`, `agent_token`, `cert_pem`, `ca_cert_pem`, `cert_expires_at`, `policy_poll_interval_sec`, `command_poll_interval_sec`.
- `POST /v1/agent/heartbeat` — heartbeat (mTLS cert / Bearer). Обновляет `last_seen_at`, `os_version`, `agent_version`, `ip_address`.
- `GET /v1/agent/commands` — получить очередь pending-команд (mTLS cert / Bearer)
- `POST /v1/agent/commands/{id}/result` — отправить результат команды (mTLS cert / Bearer)
- `GET /v1/agent/policies` — получить политики, применимые к данному агенту (mTLS cert / Bearer). Возвращает политики из прямых назначений агенту + назначений на группы агента; правила из `custom_rules` и подключённых сервисов объединяются.
- `POST /v1/agent/renew` — обновить сертификат (mTLS cert / Bearer)

---

## Политики

### Поле kind

- `traffic` — фильтрация сетевого трафика по доменам, URL, IP-адресам.
- `process` — контроль запуска исполняемых файлов на endpoint'е.

Политики разных `kind` управляются независимо: в UI разнесены по вкладкам. Сервисы тоже разделены по `kind`.

### Поле source

- `local` — создана админом филиала. Полностью редактируема. Не покидает филиал.
- `global` — создана в HQ, синхронизирована на филиалы. На филиале read-only.

### Структура правил

1. **Сервисы** — переиспользуемые именованные группы правил, подключаются через M2M `policy_services`.
2. **Кастомные правила** — поле `custom_rules` (JSONB) непосредственно в политике.

Типы правил: `domain`, `url`, `ip` (для traffic), `process` (для process).

### Разрешение конфликтов

По умолчанию побеждает global. Если `overridable=true` — локальные политики могут перебить.

### Версионирование

Глобальные политики версионируются. Синхронизация: `GET /v1/branches/policies?since_version=N`.

---

## Команды

### Фазы

**Фаза 1 — безопасные команды (пилот):** `reboot`, `collect_diagnostics`, `update_self`, `apply_config`.

**Фаза 2 — опасные команды (после пилота):** `download_file`, `run_installer`, `disable_network_interface`, `run_named_script`.

**Фаза 3 — кампании и расписание.**

### Подпись

Все команды криптографически подписываются сервером. Агент проверяет подпись публичным ключом, полученным при enrollment.

### Ограничение на стороне агента

Захардкоженный whitelist типов команд. Подписанная команда неизвестного типа отвергается.

---

## Инфраструктура и эксплуатация

### Деплой

Каждый сервер филиала — Docker Compose:
- `postgres` (16-alpine)
- `server` (umbrella-server FastAPI, порт 127.0.0.1:9090)
- nginx — на хосте (не в compose)

Volumes Docker Compose:
```yaml
- src:/app/src           # hot-reload при разработке
- alembic:/app/alembic
- pki:/app/pki           # Branch CA + сертификаты доступны с хоста
- scripts:/app/scripts   # скрипты управления (gen_nginx_cert.py и др.)
```

### PKI-операции (make-таргеты)

```
make gen-nginx-cert h=api.umbrella.su   — сгенерировать TLS-сертификат для nginx
```

### Мониторинг

Prometheus + Grafana, хостится в HQ. Серверы филиалов выставляют `/metrics`.

---

## Roadmap

### Сделано ✅

1. **`instance`** — конфиг инстанса (BranchConfig, ensure_instance при старте).
2. **`agents`** — CRUD, enrollment-токен, heartbeat, cert renewal, фильтрация.
3. **`groups`** — группировка агентов, batch-добавление.
4. **`policies`** — политики с kind/source/action/version + сервисы (M2M) + таргетинг на группы и агентов через `policy_group_assignments` / `policy_agent_assignments`.
5. **umbrella-agent TUI** — raw-mode guided wizard, verify screen, logs, service install; enrollment flow без cooked-mode.
6. **mTLS end-to-end** — Branch CA, enrollment, cert rotation, nginx config, `SetClientCert` с system root CAs + Branch CA.
7. **`BranchCA.sign_server_cert()`** — генерация TLS-сертификата nginx от Branch CA.
8. **`commands` Фаза 1** — серверная сторона: модели, очередь команд (reboot/collect_diagnostics/update_self/apply_config), dispatch, сбор результатов; API вложен под `/v1/agents/{agent_id}/commands`.

### Следующие шаги

**Ближайшее (пилотный запуск):**

- [ ] **Проверить e2e на реальном агенте** — heartbeat, poll команд, cert renewal на Windows endpoint.
- [ ] **`agents` статус** — автоматическое переключение `active`/`disabled` по `last_seen_at` (heartbeat > N минут → disabled).
- [ ] **Пилотный деплой** — 1–2 реальных филиала, 10–20 endpoint'ов.

**После пилота:**

- [ ] **`metrics`** — push телеметрии агентов (CPU, RAM, disk, процессы) на сервер.
- [ ] **`events`** — аудит-лог операций.
- [ ] **Windows MSI** — подписанный инсталлер для автоматической установки агента.
- [ ] **`commands` Фаза 2** — `download_file`, `run_installer`.
- [ ] **Enforcement** — DNS/URL-блокировка на Windows (WFP или DNS-прокси, механизм TBD).
- [ ] **`hq-server`** — новое приложение, реестр филиалов, глобальные политики.
- [ ] **Sync филиал ↔ HQ** — enrollment филиала, heartbeat, синхронизация политик.

---

## Non-goals

- **Deep Packet Inspection (DPI).** Только DNS/URL/IP. Без MITM TLS.
- **Endpoint antivirus / EDR.** Process-политики контролируют запуск по имени, не сканируют файлы.
- **Полноценный MDM.** Только desktop-агенты, без mobile.
- **Произвольное исполнение скриптов.** Скрипты предрегистрируются; никакого `eval(command_string)`.
- **Real-time контроль из HQ.** Всё идёт через сервер филиала.
- **Free-form multi-tenancy.** Одна организация, множество филиалов. Две организации = два деплоя.
- **Сертификации соответствия.** Не ISO 27001 / SOC 2.

---

## Открытые вопросы

- Точный механизм DNS-блокировки на Windows-агентах (WFP-драйвер? DNS-прокси? гибрид с hosts-файлом?).
- Механизм HQ-аутентификации для корпоративных клиентов (SAML/OIDC?).
- Сроки хранения логов на каждом слое (филиал, HQ, по типам событий).
- Модель approval flow для команд Фазы 2.
- Multi-region деплой HQ (active/passive, read-реплики?).
- Cert renewal агента: сервер должен отзывать старый сертификат при выпуске нового (CRL не реализован).
