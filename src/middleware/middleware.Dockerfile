# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

RUN apt-get -y update

WORKDIR /middleware
ENV PYTHONPATH "${PYTHONPATH}:/middleware"
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt