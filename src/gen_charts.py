import util.database as db
import logging
import sys
import datetime
import matplotlib.pyplot as plt
import japanize_matplotlib
import numpy as np
from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 現在時刻
now = datetime.datetime.utcnow()
chart_data = {}
sorted_chart_data = {}

# 過去24時間分のデータを取得
for i in range(24):
    end_time = now - datetime.timedelta(hours=i)
    start_time = end_time - datetime.timedelta(hours=1)

    # インスタンスごとの統計を取得
    avg_diff = db.get_avg_diff(start_time, end_time)
    sorted_diff = avg_diff.copy()
    sorted_diff.sort(key=lambda x: x[4], reverse=True)
    
    logger.info(f"Sorted by diff for time range: {start_time} - {end_time}")
    for instance in sorted_diff:
        logger.info(f"Instance: {instance[0]} | {instance[1]} ({instance[2]}-{instance[3]})")
        logger.info(f"Average diff: {instance[4]}s")
        logger.info("-"*10)
    chart_data[end_time] = sorted_diff # sorted_diff を格納

    # ヒートマップ生成用
    # 上位15位以外のインスタンスを除外
    filtered_diff = sorted_diff[:20]
    sorted_chart_data[end_time] = filtered_diff # filtered_diff を格納
    
# ヒートマップ用のデータ準備
instances = []
time_labels = []
heatmap_data = []
for i in range(24):
    end_time = now - datetime.timedelta(hours=i)
    start_time = end_time - datetime.timedelta(hours=1)
    time_labels.append(end_time.strftime('%H:%M'))
    sorted_diff = sorted_chart_data[end_time]
    if not instances:
        instances = [instance[0] for instance in sorted_diff]
    instance_diff_map = {instance[0]: instance[4] for instance in sorted_diff}
    diffs = []
    for instance_name in instances:
        diffs.append(instance_diff_map.get(instance_name, 0) or 0) # Use 0 if instance not present or diff is None
    heatmap_data.append(diffs)

heatmap_data = np.array(heatmap_data)

fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(heatmap_data, cmap='viridis', aspect='auto') # Use viridis colormap

# Show all ticks and label them with the instance hosts
ax.set_xticks(np.arange(len(instances)))
ax.set_xticklabels(instances)
ax.set_yticks(np.arange(len(time_labels)))
ax.set_yticklabels(time_labels)

# Rotate the tick labels and set their alignment.
plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
         rotation_mode="anchor")

# Loop over data dimensions and create text annotations.
for i in range(len(time_labels)):
    for j in range(len(instances)):
        text = ax.text(j, i, heatmap_data[i, j].round(1),
                       ha="center", va="center", color="w") # Display rounded values

ax.set_xlabel("Instance Host")
ax.set_ylabel("Time (UTC)")
ax.set_title("Federation delays by instance (Heatmap)")
fig.colorbar(im, ax=ax, label='Average delays (s)') # Add colorbar with label
plt.rcParams['font.family'] = 'IPAexGothic' # 日本語フォント設定
plt.tight_layout()
plt.savefig("avg_diff_heatmap.png", bbox_inches='tight')
logger.info(f"Heatmap chart saved to avg_diff_heatmap.png")
plt.close(fig)

# 過去1時間分のグラフを表示
fig, ax = plt.subplots()
instances = [instance[0] for instance in sorted_chart_data[now]]
diffs = [instance[4] for instance in sorted_chart_data[now]]
ax.bar(instances, diffs)
ax.set_xlabel("Instance Host")
plt.xticks(rotation=90)
plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.3)
ax.set_ylabel("Average delays (s)")
ax.set_title(f"Federation delays by instance for time range: {(now - datetime.timedelta(hours=1)).strftime('%Y-%m-%d %H:%M')}(UTC) - {now.strftime('%Y-%m-%d %H:%M')}(UTC)")
plt.tight_layout()
plt.savefig("avg_diff.png", bbox_inches='tight')
logger.info(f"Chart saved to avg_diff.png")
