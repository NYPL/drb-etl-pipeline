.DEFAULT: help

compose_file = docker-compose.yml
compose_command = docker-compose --file $(compose_file)

help:
	@echo "make help"

test: 
	python -m pytest --cov-report term-missing --cov=. tests/

allure-test:
	python -m pytest --alluredir=./allure-results ./tests

up:
	$(compose_command) up -d


