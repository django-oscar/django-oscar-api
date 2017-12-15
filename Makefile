.PHONY: test install sandbox

clean:
	find . -name '*.pyc' -delete
	find . -name '__pycache__' -delete
	find . -name '*.egg-info' -delete

install:
	pip install -e .[dev]
	pip install django-oscar-api[docs]

sandbox: install
	python sandbox/manage.py migrate
	python sandbox/manage.py loaddata product productcategory productattribute productclass productattributevalue category attributeoptiongroup attributeoption stockrecord partner voucher country

test: 
	python sandbox/manage.py test oscarapi

coverage:
	coverage run sandbox/manage.py test oscarapi
	coverage report -m
	coverage xml -i

docs: install
	pip install "Django>=1.11.0,<2.0"
	cd docs && make clean && make html

clean_release: clean
	if [ -d "dist" ]; then rm dist/*; fi

release_testpypi: clean_release
	python setup.py sdist
	twine upload --repository pypitest dist/*

release: clean_release
	python setup.py sdist
	twine upload --repository pypi dist/*
