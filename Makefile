.PHONY: clean install sandbox test coverage docs build_release, publish_release_testpypi publish_release

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -Rf *.egg-info
	rm -Rf dist/
	rm -Rf build/

install:
	pip install -e .[test,docs]

sandbox: install
	python sandbox/manage.py migrate
	python sandbox/manage.py loaddata product productcategory productattribute productclass productattributevalue category option attributeoptiongroup attributeoption stockrecord partner voucher country

test:
	python sandbox/manage.py test oscarapi --settings=sandbox.settings.nomigrations

coverage:
	coverage run sandbox/manage.py test oscarapi --settings=sandbox.settings.nomigrations
	coverage report -m
	coverage xml -i

docs: install
	pip install "Django>=1.11.0,<2.0"
	cd docs && make clean && make html

build_release: clean
	python setup.py sdist bdist_wheel

publish_release_testpypi: build_release
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

publish_release: build_release
	twine upload dist/*

.dev:
	pip install -e .[test,docs,devpy36]
	touch .dev

lint: .dev
	pylint setup.py oscarapi/
	black --check --exclude "migrations/*" setup.py oscarapi/**/*.py
