COMPOSE = docker compose

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

shell:
	$(COMPOSE) exec django bash

migrate:
	$(COMPOSE) exec django pdm run python manage.py migrate

makemigrations:
	$(COMPOSE) exec django pdm run python manage.py makemigrations

createsuperuser:
	$(COMPOSE) exec django pdm run python manage.py createsuperuser

runserver:
	$(COMPOSE) exec django pdm run python manage.py runserver 0.0.0.0:8000
