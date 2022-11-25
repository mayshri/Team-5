# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

RUN apt-get -y update
RUN apt-get -y install git
RUN python3 -m pip install --upgrade pip

WORKDIR /Team-5
ENV PYTHONPATH "${PYTHONPATH}:/Team-5"
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
WORKDIR /Team-5/src