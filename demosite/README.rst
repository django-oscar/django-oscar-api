========
Demosite
========

A demosite to demonstrate how to override a view and serializer with oscarapi.


Usage
=====

1. Clone this repository.
2. Create a virtualenv (with virtualenvwrapper) ``mkvirtualenv demosite``
3. Go to the demosite directory (``cd demosite``) and run `python setup.py develop`
4. Run the migrations: ``./manage.py migrate`` and add a superuser so you can login into oscar's dashboard: ``./manage.py createsuperuser``
5. Run ``./manage.py runserver``
6. Add a product in Oscar's dashboard
7. You will see the different view when your browse to ``http://localhost:8000/api/products/``
