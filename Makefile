.PHONY: clean install sandbox test coverage docs build_release, publish_release_testpypi publish_release

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	rm -Rf *.egg-info
	rm -Rf dist/
	rm -Rf build/

install:
	pip install -e .[dev,docs]

sandbox: install
	python sandbox/manage.py migrate
	python sandbox/manage.py loaddata product productcategory productattribute productclass productattributevalue category option attributeoptiongroup attributeoption stockrecord partner voucher country

test:
	python sandbox/manage.py test oscarapi --settings=sandbox.settings.block_admin_api_true
	python sandbox/manage.py test oscarapi --settings=sandbox.settings.block_admin_api_false

coverage:
	coverage run sandbox/manage.py test oscarapi --settings=sandbox.settings.block_admin_api_true
	coverage run sandbox/manage.py test oscarapi --settings=sandbox.settings.block_admin_api_false
	coverage report -m
	coverage xml -i

docs: install
	cd docs && make clean && make html

build_release: clean
	python setup.py sdist bdist_wheel

publish_release_testpypi: build_release
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

publish_release: build_release
	twine upload dist/*

lint.installed:
	pip install -e .[lint]
	touch $@

lint: lint.installed
	flake8 oscarapi/

black:
	black --exclude "/migrations/" oscarapi/
