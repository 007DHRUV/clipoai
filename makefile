
APP_NAME=clipoai
DOCKER_COMPOSE=docker-compose
PYTHON=python3

.PHONY: help up down logs rebuild shell api celery clean clean-all

help:  ## Show help for each command
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

up:  ## Start all containers (FastAPI, Celery, Redis, Mongo)
	$(DOCKER_COMPOSE) up -d --build

down:  ## Stop all containers
	$(DOCKER_COMPOSE) down

logs:  ## Tail logs from all services
	$(DOCKER_COMPOSE) logs -f --tail=100

api:  ## Tail logs from FastAPI container only
	$(DOCKER_COMPOSE) logs -f api

celery:  ## Tail logs from Celery worker only
	$(DOCKER_COMPOSE) logs -f celery_worker

shell:  ## Shell into FastAPI container
	$(DOCKER_COMPOSE) exec api sh

rebuild: down up  ## Rebuild and restart all containers

clean:  ## Remove uploads, thumbnails, __pycache__
	rm -rf uploads/* thumbnails/* **/__pycache__ .pytest_cache

clean-all: down clean  ## Stop containers and clean project state

