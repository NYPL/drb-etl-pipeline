.DEFAULT: help

help:
	@echo "make help"

test: 
	python -m pytest --cov-report term-missing --cov=. tests/
