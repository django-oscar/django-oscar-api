FROM ubuntu:bionic

LABEL name="oscarapi test docker image" \
      vendor="Django Oscar API" \
      maintainer="martijn@devopsconsulting.nl" \
      build-date="20191213"

RUN apt-get update
RUN apt-get -yq install sqlite3 python3 python3-pip
RUN update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1