import util.database as db
import logging
import sys
import datetime
import matplotlib.pyplot as plt
import numpy as np
from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 現在時刻
now = datetime.datetime.now()
chart_data = {}

for i in range(24):
    start_time = now - datetime.timedelta(hours=i)
    end_time = start_time + datetime.timedelta(hours=1)

    # インスタンスごとの統計を取得
    avg_diff = db.get_avg_diff(start_time, end_time)
    sorted_diff = avg_diff.copy()
    sorted_diff.sort(key=lambda x: x[4], reverse=True)

    logger.info(f"Sorted by diff for time range: {start_time} - {end_time}")
    for instance in sorted_diff:
        logger.info(f"Instance: {instance[0]} | {instance[1]} ({instance[2]}-{instance[3]})")
        logger.info(f"Average diff: {instance[4]}s")
        logger.info("-"*10)
    
    chart_data[end_time] = sorted_diff

# グラフを再帰的に生成
for end_time, sorted_diff in chart_data.items():
    start_time = end_time - datetime.timedelta(hours=1)

    fig, ax = plt.subplots()
    instances = [instance[0] for instance in sorted_diff]
    diffs = [instance[4] for instance in sorted_diff]
    ax.bar(instances, diffs)
    ax.set_xlabel("Instance Host")
    ax.set_ylabel("Average delays (s)")
    ax.set_title(f"Federation delays by instance for time range: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}")
    plt.tight_layout()

    # save
    filename = f"avg_diff_{start_time.strftime('%Y%m%d-%H')}-{end_time.strftime('%H')}.png"
    plt.savefig(filename)
    logger.info(f"Chart saved to {filename}")
    plt.close(fig) # close figure to prevent memory warning

# 過去1時間分のグラフを表示
fig, ax = plt.subplots()
instances = [instance[0] for instance in chart_data[now]]
diffs = [instance[4] for instance in chart_data[now]]
ax.bar(instances, diffs)
ax.set_xlabel("Instance Host")
ax.set_ylabel("Average delays (s)")
ax.set_title(f"Federation delays by instance for time range: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}")
plt.tight_layout()
plt.savefig("avg_diff.png")
logger.info(f"Chart saved to avg_diff.png")
