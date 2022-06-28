# syntax=docker/dockerfile:1

FROM ubuntu:22.04

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apt update 

RUN apt install -y python3-pip 

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "./app.py" ]

EXPOSE 5001



