test: typecheck pytest

pytest:
	poetry run py.test -v --cov-report term-missing --cov=impositioner

typecheck:
	poetry run pytype ./impositioner

format: isort black

black:
	poetry run black ./impositioner ./tests ./tools

isort:
	poetry run isort ./impositioner ./tests ./tools

.PHONY: init test typecheck
