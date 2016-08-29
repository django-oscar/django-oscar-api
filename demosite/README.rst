========
Demosite
========

A demosite to demonstrate how to override a view and serializer with oscarapi.


Usage
=====

1. Create a virtualenv ``mkvirtualenv demosite``
2. Go to the demosite directory and run `python setup.py develop`
3. Run the migrations: ``./manage.py migrate`` and a superuser so you can login into oscar's dashboard: ``./manage.py createsuperuser``
4. Run ``./manage.py runserver``
