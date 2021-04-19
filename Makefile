.DEFAULT: help

help:
	@echo "make help"

test: 
	python -m pytest --cov-report term-missing --cov=. tests/

allure-test:
	py.test --alluredir=/drb-etl-pipeline/allure-results/ ./tests
