install:
	python setup.py develop
	pip install -r requirements.txt

sandbox: install
	python sandbox/manage.py syncdb --noinput
	python sandbox/manage.py migrate

