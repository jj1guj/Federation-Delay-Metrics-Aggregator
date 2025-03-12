FROM python:3.10
WORKDIR /app

# install python packages
COPY ./requirements.txt /app/requirements.txt
COPY ./src/* /app/
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "main.py"]