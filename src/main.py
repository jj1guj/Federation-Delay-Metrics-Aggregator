import asyncio
import time
import datetime
from brcore import Bromine
import util.database as db
import logging
import sys
from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

INSTANCE = "shahu.ski"
brm = Bromine(instance=INSTANCE)

logger.info(f"Connecting to {INSTANCE}")


async def on_note(note: dict):
    logger.info(f"Received note: {note}")
    body = note["body"]  # body情報だけほしい
    
    
    try:
        # id
        note_id = body["id"]
        # ノート作成日時
        note_created_at = body["createdAt"]
        # 現在時刻
        note_received_at = datetime.datetime.now()
        # ノート作成日時をdatetime型に変換
        note_created_at = datetime.datetime.strptime(note_created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
        # 現在時刻とノート作成日時の差分(秒)
        diff = str(note_received_at - note_created_at)
        diff = diff.split(":")
        diff = float(diff[0]) * 3600 + float(diff[1]) * 60 + float(diff[2])
        
        
        # インスタンス情報
        instance = body["user"]["instance"]
        host = body["user"]["host"]
        
        db.insert_summary(note_id, note_created_at, note_received_at, diff, instance["name"], host, instance["softwareName"], instance["softwareVersion"])
        
        logger.info(f"Note {note_id} processed.")
        logger.info(f"Note created at: {note_created_at}")
        logger.info(f"Note received at: {note_received_at}")
        logger.info(f"Diff: {diff}s")
        logger.info(f"Instance: {instance['name']} | {host} ({instance['softwareName']}-{instance['softwareVersion']})")
    except Exception as e:
        db.insert_error(note_id, note_created_at, note_received_at, e)
        logger.error(f"Error: {e}")
        logger.error("-"*10)
        logger.error(body)
        
        pass
    
brm.ws_connect("globalTimeline", on_note)

try:
    asyncio.run(brm.main())
except KeyboardInterrupt:
    logger.info("KeyboardInterrupt")
