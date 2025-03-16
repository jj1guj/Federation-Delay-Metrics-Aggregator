import os
from typing import Optional
import config
import boto3
from botocore.config import Config
import logging
import sys
from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


s3 = boto3.client(
    "s3",
    endpoint_url=config.ENDPOINT_URL,
    aws_access_key_id=config.ACCESS_KEY_ID,
    aws_secret_access_key=config.SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
)

def upload_to_r2(file_path: str, object_name: Optional[str] = None) -> str:
    """
    ファイルをCloudflare R2にアップロードし、公開URLを返します。

    :param file_path: アップロードするファイルへのパス
    :param object_name: S3オブジェクト名。指定されない場合、file_pathのbasenameが使用されます
    :return: アップロードされたファイルの公開URL
    """
    # S3 object_nameが指定されていない場合、file_pathのbasenameを使用
    if object_name is None:
        object_name = os.path.basename(file_path)

    try:
        logger.info(f"Uploading file: {file_path} to {object_name}")
        # ファイルをアップロード
        s3.upload_file(file_path, config.BUCKET_NAME, object_name)

        # アップロードされたファイルの公開URLを生成
        url = f"{config.BUCKET_PUBLIC_URL}{object_name}"


        logger.info(f"File {file_path} uploaded to {object_name}")
        return url
    except Exception as e:
        logger.error(f"Error: {e}")
        return None
