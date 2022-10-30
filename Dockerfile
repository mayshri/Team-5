# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

RUN apt-get -y update
RUN apt-get -y install git


WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN chmod a+x script.sh

CMD ["./script.sh"]
