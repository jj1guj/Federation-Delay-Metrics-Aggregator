import asyncio
import datetime
import logging
import sys
import time
from logging import INFO, getLogger

from brcore import Bromine
from pytz import timezone

import config
import util.database as db

logger = getLogger(__name__)
logger.setLevel(INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

brm = Bromine(instance=config.INSTANCE)
logger.info(f"Connecting to {config.INSTANCE}")


# ノート受信時の処理
async def on_note(note: dict):
    logger.debug(f"Received note: {note}")
    body = note["body"]  # body情報だけほしい

    try:
        # id
        note_id = body["id"]
        # ノート作成日時
        note_created_at = datetime.datetime.strptime(body["createdAt"],
                                                     "%Y-%m-%dT%H:%M:%S.%fZ")
        # 現在時刻(UTC)
        note_received_at = datetime.datetime.utcnow()
        # 現在時刻とノート作成日時の差分(秒)
        time_diff = note_received_at - note_created_at
        diff_seconds = time_diff.total_seconds()

        # インスタンス情報
        instance = body["user"]["instance"]
        host = body["user"]["host"]

        db.insert_summary(note_id, note_created_at, note_received_at,
                          diff_seconds, instance["name"], host,
                          instance["softwareName"],
                          instance["softwareVersion"])

        logger.info(f"Note {note_id} processed.")
        logger.info(
            f"Note created at: {note_created_at.replace(tzinfo=datetime.timezone.utc).astimezone(timezone('Asia/Tokyo'))}"
        )
        logger.info(
            f"Note received at: {note_received_at.replace(tzinfo=datetime.timezone.utc).astimezone(timezone('Asia/Tokyo'))}"
        )
        logger.info(f"Diff: {diff_seconds}s")
        logger.info(
            f"Instance: {instance['name']} | {host} ({instance['softwareName']}-{instance['softwareVersion']})"
        )
    except Exception as e:
        db.insert_error(note_id, note_created_at, note_received_at, e)
        logger.error(f"Error: {e}")
        logger.error("-" * 10)
        logger.error(body)
        pass


@brm.add_comeback_deco()
async def on_comeback():
    logger.info("Reconnected")


if __name__ == '__main__':
    brm.ws_connect("globalTimeline", on_note)
    asyncio.run(brm.main())
