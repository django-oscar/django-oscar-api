.PHONY: test install sandbox

install:
	pip install -e .
	pip install django-oscar-api[test]

sandbox: install
	python sandbox/manage.py migrate
	python sandbox/manage.py loaddata product productcategory productattribute productclass productattributevalue category attributeoptiongroup attributeoption stockrecord partner voucher 

test: install
	python sandbox/manage.py test oscarapi
