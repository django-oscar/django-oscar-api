#!/usr/bin/env python
from setuptools import setup, find_packages

setup(name='django-oscar-api',
      version='0.1',
      url='https://github.com/tangentlabs/django-oscar-api',
      author="David Winterbottom",
      author_email="david.winterbottom@tangentlabs.co.uk",
      description="REST API module for django-oscar",
      long_description=open('README.rst').read(),
      keywords="Oscar, REST, API",
      license='BSD',
      packages=find_packages(exclude=['sandbox*', 'tests*']),
      include_package_data=True,
      install_requires=[
          'django-oscar>=0.4',
      ],
      # See http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Django',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: Unix',
          'Programming Language :: Python']
      )
