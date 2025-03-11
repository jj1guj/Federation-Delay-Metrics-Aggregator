FROM python:3.10.5-alpine3.16
USER root

RUN apt-get update && \
    apt-get -y install --reinstall ca-certificates && \
    apt-get -y install software-properties-common && \
    apt-get -y install fonts-ipaexfont && \
    pip install --upgrade pip

# Install Basic Packages
RUN pip install ipykernel jupyter