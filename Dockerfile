FROM python:3.10
WORKDIR /app

# install python packages
COPY ./requirements.txt ./requirements.txt
COPY ./src/ .
RUN pip install --no-cache-dir -r requirements.txt