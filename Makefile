test: typecheck pytest

pytest:
	poetry run py.test -v --cov-report term-missing --cov=impositioner

typecheck:
	poetry run pytype impositioner

black:
	poetry run black ./impositioner

isort:
	poetry run isort ./impositioner

.PHONY: init test typecheck
