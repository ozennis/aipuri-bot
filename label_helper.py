# -*- coding: utf-8 -*-
# 功能：把挑好的圖依序改名成 01-001.jpg、01-002.jpg…
#      複製到 images/，並在 labels.csv 加上「台詞空白」的列，等你填
import csv
import os
import shutil

# ===== 每集只要改這兩行 =====
EPISODE = "01"                          # 集數（固定兩位數）
SRC_DIR = "C:/aipri-frames/ep01-keep"   # 挑好的圖放在哪裡
# ============================

OUT_DIR = "images"
CSV_PATH = "labels.csv"
os.makedirs(OUT_DIR, exist_ok=True)

# 依照檔名排序（0001.jpg、0002.jpg…），所以順序就是影片的時間順序
files = sorted(f for f in os.listdir(SRC_DIR) if f.lower().endswith(".jpg"))

rows = []
for n, name in enumerate(files, start=1):
    code = f"{EPISODE}-{n:03d}"         # 例如 01-005
    shutil.copy(os.path.join(SRC_DIR, name), os.path.join(OUT_DIR, f"{code}.jpg"))
    rows.append([code, "", "", f"{code}.jpg"])   # 台詞、標籤先留空

# 寫入 labels.csv（第一次會建立檔案並加上標題列）
new_file = not os.path.exists(CSV_PATH)
with open(CSV_PATH, "a", newline="", encoding="utf-8-sig" if new_file else "utf-8") as f:
    writer = csv.writer(f)
    if new_file:
        writer.writerow(["編號", "台詞", "標籤", "檔名"])
    writer.writerows(rows)

print(f"完成！第 {EPISODE} 集共 {len(rows)} 張，請打開 labels.csv 填台詞")
