.PHONY: test install sandbox

install:
	python setup.py develop

sandbox: install
	python sandbox/manage.py syncdb --noinput
	python sandbox/manage.py migrate

test: install
	python sandbox/manage.py test oscarapi

