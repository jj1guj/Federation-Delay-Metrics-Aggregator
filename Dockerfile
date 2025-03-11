FROM python:3.10
WORKDIR /usr/src/app

# install python packages
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# setup job
RUN apt-get update && apt-get install -y vim cron
COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN /usr/bin/crontab /etc/cron.d/crontab
CMD ["cron", "-f"]
