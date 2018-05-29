from setuptools import setup, find_packages

__version__ = "1.4.0"


setup(
    # package name in pypi
    name='django-oscar-api',
    # extract version from module.
    version=__version__,
    description="REST API module for django-oscar",
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    keywords='',
    author='Lars van de Kerkhof, Martijn Jacobs',
    author_email='lars@permanentmarkers.nl, martijn@devopsconsulting.nl',
    url='https://github.com/django-oscar/django-oscar-api',
    license='BSD',
    # include all packages in the egg, except the test package.
    packages=find_packages(
        exclude=['ez_setup', 'examples', '*tests', '*fixtures', 'sandbox']),
    # for avoiding conflict have one namespace for all apc related eggs.
    namespace_packages=[],
    # include non python files
    include_package_data=True,
    zip_safe=False,
    # specify dependencies
    install_requires=[
        'setuptools',
        'django-oscar>=1.5.1',
        'djangorestframework>=3.4',
        'six'
    ],
    # mark test target to require extras.
    extras_require={
        'dev': ['django-nose', 'coverage', 'mock', 'twine'],
        'docs': ['sphinx', 'sphinx_rtd_theme'],
    },
)
