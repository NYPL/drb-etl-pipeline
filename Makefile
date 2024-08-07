.DEFAULT: help

compose_file = docker-compose.yml
compose_command = docker-compose --file $(compose_file)

help:
	@echo "make help"

unit: 
	python -m pytest --cov-report term-missing --cov=. tests/unit

allure-test:
	python -m pytest --alluredir=./allure-results ./tests/unit

integration: 
	python -m pytest tests/integration

up:
	$(compose_command) up -d

up-watch:
	$(compose_command) up

down:
	$(compose_command) down

down-clean:
	$(compose_command) down --volumes

stop:
	$(compose_command) stop
