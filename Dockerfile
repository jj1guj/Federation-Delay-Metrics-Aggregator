FROM python:3.10
WORKDIR /usr/src/app

# setup job
RUN apt-get update && apt-get install -y vim cron
COPY crontab /var/spool/cron/crontabs/root
RUN crontab /var/spool/cron/crontabs/root
CMD ["cron", "-f"]

# install python packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
