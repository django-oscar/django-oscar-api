import os

from fabric.api import *
from fabric.contrib.files import exists


def default_env():
    env.project_name = local('python setup.py --name', capture=True)
    env.project_version = local('python setup.py --version', capture=True)

@task
def test():
    default_env()

@task
def acceptance():
    default_env()

@task
def production():
    default_env()

@task
def deploy():
    execute(build_package)

@runs_once
def build_package():
    # Create distributed package
    local('python setup.py sdist')
    version = local('python setup.py --fullname', capture=True)

    # Create version.txt file
    local('echo %s > version-django-oscar-commerce-connect.txt' % version)
