import asyncio
import time
import datetime
from brcore import Bromine
import util.database as db
import logging
import sys
import os
import util.gen_charts as gen_charts
import util.s3 as s3
import schedule 
import config
from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

brm = Bromine(instance=config.INSTANCE)
logger.info(f"Connecting to {config.INSTANCE}")


# 生成/投稿を行う
async def generate_and_post():
    try:
        # 各チャートを生成
        gen_charts.generate_charts()
        
        # data.jsonとヒートマップ, チャートをアップロード
        s3.upload_to_r2("output/data.json", "data.json")
        s3.upload_to_r2("output/avg_diff_heatmap.png", "heatmap.png")
        s3.upload_to_r2("output/avg_diff.png", "chart.png")
        
        # インスタンス別のチャートをアップロード(output/instances/{host}.png)
        for host in os.listdir("output/instances"):
            s3.upload_to_r2(f"output/instances/{host}", f"instance/{host}")
    except Exception as e:
        logger.error(f"Error: {e}")
        return       
    else:
        return


# ノート受信時の処理
async def on_note(note: dict):
    logger.info(f"Received note: {note}")
    body = note["body"]  # body情報だけほしい
    
    
    try:
        # id
        note_id = body["id"]
        # ノート作成日時
        note_created_at = datetime.datetime.strptime(body["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
        # 現在時刻(UTC)
        note_received_at = datetime.datetime.utcnow()
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

# メインループ
async def main():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)
        
# jobの設定
logger.info("Setting up job")
schedule.every().hours.at(":00").do(generate_and_post)
            
brm.ws_connect("globalTimeline", on_note)


try:
    asyncio.create_task(main())
    asyncio.run(brm.main())
except KeyboardInterrupt:
    logger.info("KeyboardInterrupt")
