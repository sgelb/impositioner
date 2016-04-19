init:
	    pip install -r requirements.txt

test:
	    py.test -v --cov-report term-missing --cov=impositioner

