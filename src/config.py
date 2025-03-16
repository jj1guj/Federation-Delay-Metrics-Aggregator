import os
from dotenv import load_dotenv
from os.path import join, dirname

load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

INSTANCE = os.environ.get("INSTANCE", "shahu.ski")
MISSKEY_TOKEN = os.environ.get("MISSKEY_TOKEN")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
PREFIX = os.environ.get("PREFIX")
BUCKET_PUBLIC_URL = os.environ.get("BUCKET_PUBLIC_URL")
ENDPOINT_URL = os.environ.get("ENDPOINT_URL")
ACCESS_KEY_ID = os.environ.get("ACCESS_KEY_ID")
SECRET_ACCESS_KEY = os.environ.get("SECRET_ACCESS_KEY")
