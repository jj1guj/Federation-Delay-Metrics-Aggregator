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
from pytz import timezone
from misskey import Misskey
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

def log_get_job():
    joblist = schedule.get_jobs()
    for job in joblist:
        logger.info(f"Next run: {job.next_run}")

# 生成/投稿を行う
def generate_and_post():
    logger.info("Job start.")
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
            
        
        mi = Misskey(config.INSTANCE, config.MISSKEY_TOKEN)
        # ドライブへ画像のアップロード
        logger.info("Uploading files to drive")
        with open("output/data.json", "rb") as f:
            mi_data = mi.drive_files_create(f)
        with open("output/avg_diff_heatmap.png", "rb") as f:
            mi_heatmap = mi.drive_files_create(f)
        with open("output/avg_diff.png", "rb") as f:
            mi_chart = mi.drive_files_create(f)
        
        # 投稿
        logger.info("Posting note")
        mi.notes_create(text="""
各連合先の配送遅延情報が更新されました。

インスタンス毎のチャートは`https://fdma.shahu.ski/report/instance/{host}.png`から確認できます。
[GitHub](https://github.com/team-shahu/Federation-Delay-Metrics-Aggregator)
                        """, 
                        file_ids=[mi_chart["id"], mi_heatmap["id"], mi_data["id"]], visibility="home")
        logger.info("Posted note")
        
        # ファイルの削除
        logger.info("Deleting files")
        os.remove("output/data.json")
        os.remove("output/avg_diff_heatmap.png")
        os.remove("output/avg_diff.png")
        for host in os.listdir("output/instances"):
            os.remove(f"output/instances/{host}")
        logger.info("Files deleted")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        log_get_job()
        return       
    else:
        logger.info("Job done.")
        log_get_job()
        return


# ノート受信時の処理
async def on_note(note: dict):
    logger.debug(f"Received note: {note}")
    body = note["body"]  # body情報だけほしい
    
    
    try:
        # id
        note_id = body["id"]
        # ノート作成日時
        note_created_at = datetime.datetime.strptime(body["createdAt"], "%Y-%m-%dT%H:%M:%S.%fZ")
        # 現在時刻(UTC)
        note_received_at = datetime.datetime.utcnow()
        # 現在時刻とノート作成日時の差分(秒)
        time_diff = note_received_at - note_created_at
        diff_seconds = time_diff.total_seconds()

        # インスタンス情報
        instance = body["user"]["instance"]
        host = body["user"]["host"]
        
        db.insert_summary(note_id, note_created_at, note_received_at, diff_seconds, instance["name"], host, instance["softwareName"], instance["softwareVersion"])
        
        logger.info(f"Note {note_id} processed.")
        logger.info(f"Note created at: {note_created_at.replace(tzinfo=datetime.timezone.utc).astimezone(timezone('Asia/Tokyo'))}")
        logger.info(f"Note received at: {note_received_at.replace(tzinfo=datetime.timezone.utc).astimezone(timezone('Asia/Tokyo'))}")
        logger.info(f"Diff: {diff_seconds}s")
        logger.info(f"Instance: {instance['name']} | {host} ({instance['softwareName']}-{instance['softwareVersion']})")
    except Exception as e:
        db.insert_error(note_id, note_created_at, note_received_at, e)
        logger.error(f"Error: {e}")
        logger.error("-"*10)
        logger.error(body)
        
        pass


@brm.add_comeback_deco()
async def on_comeback():
    logger.info("Reconnected")


async def main_loop():
    schedule.every().hour.at(":00").do(generate_and_post)
    logger.info("Scheduled job: generate_and_post")
    log_get_job()

    brm.ws_connect("globalTimeline", on_note)
    asyncio.create_task(brm.main())

    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main_loop())
