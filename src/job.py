import datetime
import logging
import os
import sys
import time
from logging import INFO, getLogger

import schedule
from misskey import Misskey

import config
import util.gen_charts as gen_charts
import util.s3 as s3
import web

logger = getLogger(__name__)
logger.setLevel(INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


def log_get_job():
    joblist = schedule.get_jobs()
    for job in joblist:
        logger.info(f"Next run: {job.next_run}")


# 生成/投稿を行う
def generate_and_post():
    logger.info("Job start.")
    try:
        time = datetime.datetime.now().strftime("%Y年%m月%d日%H時")
        # 各チャートを生成
        gen_charts.generate_charts()

        # data.jsonとヒートマップ, チャートをアップロード
        s3.upload_to_r2("output/data.json", f"{config.PREFIX}/data.json")
        s3.upload_to_r2("output/avg_diff_heatmap.png",
                        f"{config.PREFIX}/heatmap.png")
        s3.upload_to_r2("output/avg_diff.png", f"{config.PREFIX}/chart.png")

        # インスタンス別のチャートをアップロード(output/instances/{host}.png)
        for host in os.listdir("output/instances"):
            s3.upload_to_r2(f"output/instances/{host}",
                            f"{config.PREFIX}/instance/{host}")

        # 更新後のWebページを作成
        web.generate_fdma_gallery()

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
        mi.notes_create(
            text=f"""
各連合先の配送遅延情報が更新されました。
{time}現在の情報です。

インスタンス毎のチャートは{config.BUCKET_PUBLIC_URL}/index.html から確認できます。
[GitHub](https://github.com/team-shahu/Federation-Delay-Metrics-Aggregator)

#配送遅延 #FDMA #Federation-Delay-Metrics-Aggregator
                        """,
            file_ids=[mi_chart["id"], mi_heatmap["id"], mi_data["id"]],
            visibility="home")
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


if __name__ == "__main__":
    schedule.every().hour.at(":00").do(generate_and_post)
    log_get_job()

    while True:
        schedule.run_pending()
        time.sleep(1)
