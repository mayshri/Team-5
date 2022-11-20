# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

RUN apt-get -y update
RUN apt-get -y install git


WORKDIR /

RUN pip3 install  Flask==2.2.2 requests wrapt_timeout_decorator

COPY . .
CMD [ "python3", "-m" , "flask", "--app", "middleware.py", "run", "--host=0.0.0.0", "--port=8048"]