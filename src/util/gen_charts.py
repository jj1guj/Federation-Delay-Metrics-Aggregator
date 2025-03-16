import util.database as db
import logging
import sys
import os
import datetime
import matplotlib.pyplot as plt
import japanize_matplotlib
import numpy as np
import json
import config
from pytz import timezone
from logging import getLogger, INFO
logger = getLogger(__name__)
logger.setLevel(INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# ディレクトリがなければ生成
if os.path.exists('output') == False:
    os.makedirs('output')
if os.path.exists('output/instances') == False:
    os.makedirs('output/instances')

def generate_charts():
    # 現在時刻
    now = datetime.datetime.utcnow()
    instance_data = {}
    sorted_chart_data = {}
    
    data = {
        "last_updated": now.replace(tzinfo=datetime.timezone.utc).astimezone(timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S'),
        "source_instance": config.INSTANCE,
        "charts": {
            "heatmap": f"{config.BUCKET_PUBLIC_URL}/{config.PREFIX}/heatmap.png",
            "bar_chart": f"{config.BUCKET_PUBLIC_URL}/{config.PREFIX}/chart.png"
        },
        "data": {}
    }

    # 過去24時間分のデータを取得
    for i in range(23, -1, -1):
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

        # ヒートマップ生成用
        # 上位15位以外のインスタンスを除外
        filtered_diff = sorted_diff[:20]
        sorted_chart_data[start_time] = filtered_diff # filtered_diff を格納
        
        # インスタンスごとのデータを格納
        for instance in sorted_diff:
            instance_host = instance[1]
            avg_delay = instance[4]
            if instance_host not in instance_data:
                instance_data[instance_host] = {'time_labels': [], 'delay_values': []}
            time_label = start_time.replace(tzinfo=datetime.timezone.utc).astimezone(timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H')
            instance_data[instance_host]['time_labels'].append(time_label)
            instance_data[instance_host]['delay_values'].append(avg_delay)


            
            # 観測しているインスタンスのhost, name, version, deff, created_atをすべて統合しjson形式で返す
            if instance[1] not in data["data"]:
                data["data"][instance[1]] = {
                    "name": str(instance[0]),
                    "host": str(instance[1]),
                    "version": f"{instance[2]}-{instance[3]}",
                    "chart_url": str(f"{config.BUCKET_PUBLIC_URL}/{config.PREFIX}/instance/{instance[1]}.png"),
                    "details": []
                }
            data["data"][instance[1]]["details"].append({
                "delay_sec": str(instance[4]),
                "start_time": start_time.replace(tzinfo=datetime.timezone.utc).astimezone(timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S'),
                "end_time": end_time.replace(tzinfo=datetime.timezone.utc).astimezone(timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S'),
            })
        
    # ファイルに保存
    with open('output/data.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, indent=4, ensure_ascii=False))
        

        
    # ヒートマップ用のデータ準備
    instances = []
    time_labels = []
    heatmap_data = []
    for i in range(24):
        end_time = now - datetime.timedelta(hours=i)
        start_time = end_time - datetime.timedelta(hours=1)
        time_labels.append(start_time.replace(tzinfo=datetime.timezone.utc).astimezone(timezone('Asia/Tokyo')).strftime('%H'))
        sorted_diff = sorted_chart_data[start_time]
        if not instances:
            instances = [instance[1] for instance in sorted_diff]
        instance_diff_map = {instance[1]: instance[4] for instance in sorted_diff}
        diffs = []
        for instance_name in instances:
            diffs.append(instance_diff_map.get(instance_name, 0) or 0) # Use 0 if instance not present or diff is None
        heatmap_data.append(diffs)
        
    try:
        # ヒートマップ生成
        logger.info("Generating heatmap...")
        
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
        ax.set_ylabel("Time")
        ax.set_title("Federation delays by instance (Heatmap)")
        fig.colorbar(im, ax=ax, label='Average delays (s)') # Add colorbar with label
        plt.rcParams['font.family'] = 'IPAexGothic' # 日本語フォント設定
        plt.tight_layout()
        plt.savefig("./output/avg_diff_heatmap.png", bbox_inches='tight')
        logger.info(f"Heatmap chart saved to ./output/avg_diff_heatmap.png")
        plt.close(fig)
    except Exception as e:
        logger.error(f"Error generating heatmap: {e}")
        logger.error("Skipping heatmap generation.")
        logger.error("-"*10)
        pass
    else:
        logger.info(f"Heatmap generated successfully.")


    try:
        # 過去1時間分のグラフを上位15位で生成
        fig, ax = plt.subplots()
        instances = [instance[1] for instance in sorted_chart_data[now - datetime.timedelta(hours=1)]]
        diffs = [instance[4] for instance in sorted_chart_data[now - datetime.timedelta(hours=1)]]
        ax.bar(instances, diffs)
        ax.set_xlabel("Instance Host")
        plt.xticks(rotation=90)
        plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.3)
        ax.set_ylabel("Average delays (s)")
        ax.set_title(f"Federation delays by instance for time range: {(now - datetime.timedelta(hours=1)).replace(tzinfo=datetime.timezone.utc).astimezone(timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H')} - {now.replace(tzinfo=datetime.timezone.utc).astimezone(timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H')}")
        plt.tight_layout()
        plt.savefig("./output/avg_diff.png", bbox_inches='tight')
        logger.info(f"Chart saved to ./output/avg_diff.png")
        plt.close(fig)
    except Exception as e:
        logger.error(f"Error generating bar chart: {e}")
        logger.error("Skipping bar chart generation.")
        logger.error("-"*10)
        pass
    else:
        logger.info(f"Bar chart generated successfully.")


    try:
        # インスタンスごとに折れ線グラフを生成
        for instance_host, data in instance_data.items():
            if not data['time_labels']:
                logger.warning(f"No data for instance: {instance_host}, skipping chart generation.")
                continue
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(data['time_labels'], data['delay_values'], marker='o')
            ax.set_xlabel("Time")
            ax.set_ylabel("Average Delay (s)")
            ax.set_title(f"Federation Delays for {instance_host} (Past 24 Hours)")
            plt.xticks(rotation=45, ha='right')
            # データラベルを表示
            for i, txt in enumerate(data['delay_values']):
                ax.annotate(f"{txt:.1f}s", (data['time_labels'][i], data['delay_values'][i]), textcoords="offset points", xytext=(0,10), ha='center')
            plt.tight_layout()
            plt.savefig(f"./output/instances/{instance_host}.png", bbox_inches='tight')
            logger.info(f"Line chart saved to ./output/instances/{instance_host}.png")
            plt.close(fig)
    except Exception as e:
        logger.error(f"Error generating instance line charts: {e}")
        logger.error("Skipping instance line chart generation.")
        logger.error("-"*10)
        pass
    else:
        logger.info(f"Instance line charts generated successfully.")
