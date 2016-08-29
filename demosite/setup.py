"""
A demosite with oscarapi for demo and documentation purposes
"""
from setuptools import setup, find_packages
import os

__version__ = "0.0.1"

setup(
    name='oscarapi-demosite',
    version=__version__,
    description="OscarAPI Demosite",
    long_description=__doc__,
    classifiers=[],
    keywords='',
    author='Martijn Jacobs',
    author_email='martijn@devopsconsulting.nl',
    url='https://github.com/django-oscar/django-oscar-api/demosite',
    license='Copyright',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=[],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'django-oscar-api',
        'django>=1.9, <1.10',
        'django-oscar>=1.3'
    ],
)
