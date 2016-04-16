init:
	    pip install -r requirements.txt

test:
	    ${VIRTUAL_ENV}/bin/py.test -v --cov-report term-missing --cov=impositioner

