FROM python:3.8-slim-buster
WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD python3 main.py
