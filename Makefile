test: typecheck pytest

pytest:
	poetry run py.test -v --cov-report term-missing --cov=impositioner

typecheck:
	poetry run pytype impositioner

.PHONY: init test typecheck
