from setuptools import find_packages, setup

__version__ = "2.1.1"

setup(
    # package name in pypi
    name="django-oscar-api",
    # extract version from module.
    version=__version__,
    description="REST API module for django-oscar",
    long_description=open("README.rst").read(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    python_requires=">=3.6",
    keywords="",
    author="Lars van de Kerkhof, Martijn Jacobs",
    author_email="lars@permanentmarkers.nl, martijn@devopsconsulting.nl",
    url="https://github.com/django-oscar/django-oscar-api",
    license="BSD",
    packages=find_packages(
        exclude=[
            "*tests.unit",
            "*tests.serializers*",
            "*tests.doctests*",
            "*fixtures",
            "*fixtures*",
            "*sandbox*",
        ]
    ),
    # include non python files
    include_package_data=True,
    zip_safe=False,
    # specify dependencies
    install_requires=[
        "setuptools",
        "django-oscar>=3.0",
        "Django>=2.2.13",  # CVE-2020-9402
        "djangorestframework>=3.9",  # first version to support Django 2.2
    ],
    # mark test target to require extras.
    extras_require={
        "dev": ["coverage", "mock", "twine", "wheel", "easy_thumbnails"],
        "lint": ["flake8", "flake8-black", "flake8-bugbear", "black>=19.10b0"],
    },
)
