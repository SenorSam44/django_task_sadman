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

test:
	$(COMPOSE) exec django pdm run pytest -v

report:
	$(COMPOSE) exec django pdm run python manage.py generate_report --booking_system_id=$(id) --start_date=$(start) --end_date=$(end)
