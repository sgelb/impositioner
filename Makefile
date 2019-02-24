run:
	poetry run impositioner

test:
	poetry run py.test -v --cov-report term-missing --cov=impositioner

.PHONY: init test
