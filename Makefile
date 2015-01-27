.PHONY: test install sandbox

install:
	python setup.py develop
	pip install django-oscar-api[test]

sandbox: install
	python sandbox/manage.py syncdb --noinput
	python sandbox/manage.py migrate

test: install
	python sandbox/manage.py test oscarapi

