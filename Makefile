COMPOSE_FILE := infra/docker/docker-compose.yml
SECRETS_FILE := infra/secrets/.env
APP_DIR      := apps/umbrella-server
WEB_DIR      := apps/umbrella-web
COMPOSE      := docker compose --env-file $(SECRETS_FILE) -f $(COMPOSE_FILE)

s ?= server

# ── Colors ────────────────────────────────────────────────────────────────────
_R  := \033[0m
_B  := \033[1m
_G  := \033[32m
_Y  := \033[33m
_C  := \033[36m
_RE := \033[31m
_GR := \033[90m

.DEFAULT_GOAL := help

# ── Help ──────────────────────────────────────────────────────────────────────
.PHONY: help
help:
	@printf "\n$(_B)  Umbrella$(_R)  — управление стеком\n\n"
	@printf "$(_C)  Стек$(_R)  $(_GR)────────────────────────────────────────────────$(_R)\n"
	@printf "  $(_G)%-18s$(_R) %s\n" "up"       "Поднять стек в фоне"
	@printf "  $(_G)%-18s$(_R) %s\n" "down"     "Остановить стек"
	@printf "  $(_G)%-18s$(_R) %s\n" "restart"  "Перезапустить стек"
	@printf "  $(_G)%-18s$(_R) %s\n" "build"    "Пересобрать образы"
	@printf "  $(_G)%-18s$(_R) %s\n" "rebuild"  "Пересобрать с нуля и поднять"
	@printf "  $(_G)%-18s$(_R) %s\n" "ps"       "Статус сервисов"
	@printf "\n$(_C)  Разработка$(_R)  $(_GR)──────────────────────────────────────$(_R)\n"
	@printf "  $(_G)%-18s$(_R) %s\n"                  "dev"       "Бэкенд + фронтенд локально"
	@printf "  $(_G)%-18s$(_R) %-36s $(_GR)%s$(_R)\n" "dev-back" "Локальный бэкенд (pdm)"   ":9090"
	@printf "  $(_G)%-18s$(_R) %-36s $(_GR)%s$(_R)\n" "dev-front" "Локальный фронтенд (yarn)" ":5173"
	@printf "  $(_G)%-18s$(_R) %-36s $(_GR)%s$(_R)\n" "logs"     "Логи сервиса"             "[s=server]"
	@printf "  $(_G)%-18s$(_R) %s\n"                  "logs-all" "Логи всех сервисов"
	@printf "  $(_G)%-18s$(_R) %-36s $(_GR)%s$(_R)\n" "shell"    "Войти в контейнер"        "[s=server]"
	@printf "  $(_G)%-18s$(_R) %s\n"                  "db"       "psql в postgres"
	@printf "\n$(_C)  Миграции$(_R)  $(_GR)────────────────────────────────────────$(_R)\n"
	@printf "  $(_G)%-18s$(_R) %s\n"                     "migrate"       "Применить миграции (в контейнере)"
	@printf "  $(_G)%-18s$(_R) %s\n"                     "migrate-local" "Применить миграции (pdm локально)"
	@printf "  $(_G)%-18s$(_R) %-36s $(_GR)%s$(_R)\n"   "migration"     "Создать миграцию (pdm)"   "m='описание'"
	@printf "  $(_G)%-18s$(_R) %s\n"                     "downgrade"     "Откатить последнюю миграцию"
	@printf "\n$(_C)  Качество$(_R)  $(_GR)─────────────────────────────────────────$(_R)\n"
	@printf "  $(_G)%-18s$(_R) %s\n" "lint"      "ruff check"
	@printf "  $(_G)%-18s$(_R) %s\n" "fmt"       "ruff format"
	@printf "  $(_G)%-18s$(_R) %s\n" "typecheck" "mypy"
	@printf "  $(_G)%-18s$(_R) %s\n" "test"      "pytest"
	@printf "\n$(_C)  PKI$(_R)  $(_GR)─────────────────────────────────────────────────$(_R)\n"
	@printf "  $(_G)%-18s$(_R) %-36s $(_GR)%s$(_R)\n" "gen-nginx-cert" "Сертификат nginx от Branch CA" "h=hostname"
	@printf "\n$(_C)  Очистка$(_R)  $(_GR)──────────────────────────────────────────$(_R)\n"
	@printf "  $(_G)%-18s$(_R) %s  $(_RE)%s$(_R)\n" "clean" "Остановить и удалить volumes" "⚠ сотрёт БД"
	@printf "  $(_G)%-18s$(_R) %s\n"               "prune" "Удалить висящие образы и сети"
	@printf "\n$(_GR)  Примеры:  make logs s=postgres   make migration m='add users'$(_R)\n\n"

# ── Стек ──────────────────────────────────────────────────────────────────────
.PHONY: up
up:
	@printf "$(_C)  → Поднимаю стек...$(_R)\n"
	@$(COMPOSE) up -d
	@printf "\n$(_G)  ✓ Стек запущен$(_R)\n"
	@printf "$(_GR)    Server  $(_R)http://localhost:9090\n"
	@printf "$(_GR)    Docs    $(_R)http://localhost:9090/docs\n"
	@printf "$(_GR)    Logs    $(_R)make logs\n\n"

.PHONY: down
down:
	@printf "$(_C)  → Останавливаю стек...$(_R)\n"
	@$(COMPOSE) down
	@printf "$(_G)  ✓ Готово$(_R)\n\n"

.PHONY: restart
restart: down up

.PHONY: build
build:
	@printf "$(_C)  → Собираю образы...$(_R)\n"
	@$(COMPOSE) build
	@printf "$(_G)  ✓ Образы собраны$(_R)\n\n"

.PHONY: rebuild
rebuild:
	@printf "$(_C)  → Пересобираю с нуля...$(_R)\n"
	@$(COMPOSE) build --no-cache
	@$(COMPOSE) up -d
	@printf "\n$(_G)  ✓ Готово$(_R)\n\n"

.PHONY: ps
ps:
	@$(COMPOSE) ps

# ── Разработка ────────────────────────────────────────────────────────────────
.PHONY: dev
dev:
	@printf "$(_C)  → Запускаю бэкенд и фронтенд локально...$(_R)\n\n"
	@cd $(APP_DIR) && pdm run dev & cd $(WEB_DIR) && yarn dev

.PHONY: dev-back
dev-back:
	@printf "$(_C)  → Запускаю бэкенд локально на :9090...$(_R)\n\n"
	@cd $(APP_DIR) && pdm run dev

.PHONY: dev-front
dev-front:
	@printf "$(_C)  → Запускаю фронтенд локально на :5173...$(_R)\n\n"
	@cd $(WEB_DIR) && yarn dev

.PHONY: logs
logs:
	@$(COMPOSE) logs -f --tail=100 $(s)

.PHONY: logs-all
logs-all:
	@$(COMPOSE) logs -f --tail=100

.PHONY: shell
shell:
	@$(COMPOSE) exec $(s) bash

.PHONY: db
db:
	@$(COMPOSE) exec postgres sh -c 'psql -U $$POSTGRES_USER $$POSTGRES_DB'

# ── Миграции ──────────────────────────────────────────────────────────────────
.PHONY: migrate
migrate:
	@printf "$(_C)  → Применяю миграции...$(_R)\n"
	@$(COMPOSE) exec server alembic upgrade head
	@printf "$(_G)  ✓ Миграции применены$(_R)\n\n"

.PHONY: migrate-local
migrate-local:
	@printf "$(_C)  → Применяю миграции локально...$(_R)\n\n"
	@cd $(APP_DIR) && pdm run migrate
	@printf "\n$(_G)  ✓ Готово$(_R)\n\n"

.PHONY: migration
migration:
	@test -n "$(m)" || (printf "$(_RE)  ✗ Укажи описание: make migration m='описание'$(_R)\n\n" && exit 1)
	@printf "$(_C)  → Создаю миграцию: $(_B)$(m)$(_R)$(_C)...$(_R)\n"
	@cd $(APP_DIR) && pdm run migration "$(m)"
	@printf "$(_G)  ✓ Миграция создана$(_R)\n\n"

.PHONY: downgrade
downgrade:
	@printf "$(_Y)  → Откатываю последнюю миграцию...$(_R)\n"
	@cd $(APP_DIR) && pdm run alembic downgrade -1
	@printf "$(_G)  ✓ Готово$(_R)\n\n"

# ── Качество ──────────────────────────────────────────────────────────────────
.PHONY: lint
lint:
	@cd $(APP_DIR) && pdm run lint

.PHONY: fmt
fmt:
	@cd $(APP_DIR) && pdm run fmt

.PHONY: typecheck
typecheck:
	@cd $(APP_DIR) && pdm run typecheck

.PHONY: test
test:
	@cd $(APP_DIR) && pdm run test

# ── PKI ───────────────────────────────────────────────────────────────────────
.PHONY: gen-nginx-cert
gen-nginx-cert:
	@test -n "$(h)" || (printf "$(_RE)  ✗ Укажи хост: make gen-nginx-cert h=api.umbrella.su$(_R)\n\n" && exit 1)
	@printf "$(_C)  → Генерирую TLS-сертификат сервера для $(_B)$(h)$(_R)$(_C)...$(_R)\n\n"
	@$(COMPOSE) exec server python scripts/gen_nginx_cert.py $(h)
	@printf "\n$(_G)  ✓ Файлы в apps/umbrella-server/pki/$(_R)\n\n"

# ── Очистка ───────────────────────────────────────────────────────────────────
.PHONY: clean
clean:
	@printf "$(_RE)  ⚠  Это удалит все volumes (БД и все данные)$(_R)\n"
	@printf "$(_Y)  Продолжить? [y/N]$(_R) "; \
	 read ans && [ "$$ans" = "y" ] || (printf "$(_GR)  Отменено$(_R)\n\n" && exit 1)
	@$(COMPOSE) down -v
	@printf "$(_G)  ✓ Стек остановлен, volumes удалены$(_R)\n\n"

.PHONY: prune
prune:
	@printf "$(_C)  → Очищаю Docker...$(_R)\n"
	@docker system prune -f
	@printf "$(_G)  ✓ Готово$(_R)\n\n"
