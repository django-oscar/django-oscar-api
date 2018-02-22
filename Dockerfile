FROM python:3.5
ENV PYTHONUNBUFFERED 0

# Set Code Dir
RUN mkdir /code
WORKDIR /code

# Install Django
RUN pip install "Django<2.0"

# Add source
ADD . /code/

# Install other deps
RUN make install

# Run tests
CMD make test
