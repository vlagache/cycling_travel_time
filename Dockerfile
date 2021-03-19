FROM python:3.7-slim

RUN mkdir /app
WORKDIR /app
RUN mkdir ./models


COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY ./prediction /app/prediction

CMD python -m prediction