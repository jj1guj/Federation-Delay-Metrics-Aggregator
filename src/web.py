import os

import config
import util.s3 as s3


def generate_fdma_gallery():
    prefix = f"{config.PREFIX}/instance"
    files = s3.list_r2_files(prefix=prefix)

    png_files = [f for f in files if f['Key'].lower().endswith('.png')]
    print(f"{len(png_files)} 個のPNG画像が見つかりました")

    if not png_files:
        print("PNG画像が見つかりませんでした。")
        return False

    # ソート(UTC)
    png_files.sort(key=lambda x: x['LastModified'], reverse=True)

    # 必要な情報を付加
    for img in png_files:
        img['URL'] = f"{config.BUCKET_PUBLIC_URL}{img['Key']}"
        filename = img['Key'].split('/')[-1]
        img['Hostname'] = filename.replace('.png', '')
        # ISO 8601文字列(UTC)
        img['UtcIso'] = img['LastModified'].isoformat()

    # 最終更新(UTC)を文字列化 (サーバー側ではそのまま表示)
    if png_files:
        last_updated_utc_dt = png_files[0]['LastModified']
        last_updated_utc_str = last_updated_utc_dt.strftime(
            '%Y-%m-%d %H:%M:%S')
        last_updated_utc_iso = last_updated_utc_dt.isoformat()
    else:
        last_updated_utc_str = '不明'
        last_updated_utc_iso = ''

    output_path = os.path.join('output/index.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(
            generate_html(png_files, last_updated_utc_str,
                          last_updated_utc_iso))

    s3.upload_to_r2(output_path, 'index.html')
    s3.upload_to_r2('_static/style.css', 'static/style.css')
    s3.upload_to_r2('_static/scripts.js', 'static/scripts.js')
    os.remove(output_path)

    return True


def generate_html(images, last_updated_utc_str, last_updated_utc_iso):
    html_content = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{config.INSTANCE}配送遅延時間一覧</title>
  <link rel="stylesheet" href="static/style.css">
</head>
<body>
<div class="container">
  <h1>{config.INSTANCE}配送遅延時間一覧</h1>
  <div class="controls">
    <input type="text" class="search-box" id="searchBox" placeholder="ホスト名で検索...">
    <div class="sort-options">
      <button class="sort-btn active" data-sort="date-desc">新しい順</button>
      <button class="sort-btn" data-sort="date-asc">古い順</button>
      <button class="sort-btn" data-sort="name-asc">ホスト名順</button>
      <button class="sort-btn" data-sort="size-desc">サイズ大きい順</button>
    </div>
  </div>
  <div class="gallery-stats">
    <p>インスタンス数: <span id="imageCount">{len(images)}</span></p>
    <p id="lastUpdated" data-utc="{last_updated_utc_iso}">最終更新: {last_updated_utc_str} (UTC)</p>
  </div>
  <div class="gallery" id="imageGallery">{generate_image_cards(images)}</div>
  <div id="imageModal" class="modal">
    <span class="close-modal">&times;</span>
    <div class="modal-content">
      <img src="" class="modal-image" id="modalImage">
      <div class="modal-info" id="modalInfo"></div>
    </div>
  </div>
</div>
<script src="static/scripts.js"></script>
</body>
</html>"""
    return html_content


def generate_image_cards(images):
    cards_html = ""
    for img in images:
        size_kb = img['Size'] // 1024
        cards_html += f"""<div class="image-card"
   data-hostname="{img['Hostname']}"
   data-size="{img['Size']}"
   data-date="{img['UtcIso']}"
   data-url="{img['URL']}">
  <div class="image-container">
    <img src="{img['URL']}" alt="{img['Hostname']}" loading="lazy">
  </div>
  <div class="image-info">
    <div class="hostname">{img['Hostname']}</div>
    <div class="image-meta">
      <div>サイズ: {size_kb} KB</div>
      <div class="update-utc" data-utc="{img['UtcIso']}">更新(UTC): {img['LastModified'].strftime('%Y-%m-%d')}</div>
    </div>
  </div>
</div>"""
    return cards_html


if __name__ == "__main__":
    generate_fdma_gallery()
