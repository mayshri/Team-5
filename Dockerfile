# syntax=docker/dockerfile:1

FROM dependency

RUN apt-get -y update
RUN apt-get -y install git
RUN python3 -m pip install --upgrade pip

ENV PYTHONPATH "${PYTHONPATH}:/Team-5"

WORKDIR /Team-5
COPY . .
RUN pip3 install -r requirements.txt

WORKDIR /Team-5/src
