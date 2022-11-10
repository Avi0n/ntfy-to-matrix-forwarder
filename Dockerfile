# To build the image, run `docker build` command from the root of the
# repository:
#
#    docker build -f Dockerfile .
#

##
## Creating a builder container
##

# We use an initial docker container to build all of the runtime dependencies,
# then transfer those dependencies to the container we're going to ship,
# before throwing this one away

FROM python:3.10-bullseye AS build-image
ARG DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    gcc \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    libxml2-dev \
    libxslt-dev \
    python3-dev \
    python3-venv \
    python3-pip \
    python3-wheel \
    libolm-dev

RUN python3 -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

# Install requirements
COPY requirements.txt .
RUN pip3 install --upgrade pip && pip3 install setuptools wheel && pip3 install -r requirements.txt

##
## Creating the runtime container
##

# Create the container we'll actually ship. We need to copy libolm and any
# python dependencies that we built above to this container
FROM python:3.10-slim-bullseye
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y python3-venv libolm-dev
COPY --from=build-image /opt/venv /opt/venv

WORKDIR /opt/ntfy-to-matrix
#COPY bot/ .
COPY config.yaml .
COPY main.py .

# Make sure we use the virtualenv
ENV PATH="/opt/venv/bin:$PATH"
CMD [ "python3", "-u", "main.py" ]
