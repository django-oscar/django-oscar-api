from setuptools import setup, find_packages


__version__ = "0.0.10"


setup(
    # package name in pypi
    name='django-oscar-commerce-connect',
    # extract version from module.
    version=__version__,
    description="REST API module for django-oscar",
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: Unix',
        'Programming Language :: Python']
    ),
    keywords='',
    author='Lars van de Kerkhof, Martijn Jacobs',
    author_email='lars@permanentmarkers.nl, martijn@devopsconsulting.nl',
    url='https://github.com/tangentlabs/django-oscar-api',
    license='BSD',
    # include all packages in the egg, except the test package.
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    # for avoiding conflict have one namespace for all apc related eggs.
    namespace_packages=[],
    # include non python files
    include_package_data=True,
    zip_safe=False,
    # specify dependencies
    install_requires=[
        'setuptools',
        'django-oscar',
        'djangorestframework<3.0.0'
    ],
    # mark test target to require extras.
    extras_require={
        'test': []
    },
)
