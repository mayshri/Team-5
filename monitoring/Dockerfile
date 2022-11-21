
FROM python:3.8.12-slim-buster

# set working directory
WORKDIR /app

RUN apt-get -y update
RUN apt-get -y install git

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# add and install requirements
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt

COPY cache/ /app/cache/
COPY online_evaluation.py /app/online_evaluation.py

CMD ["python", "-u", "online_evaluation.py"], "--no_mock_data"]