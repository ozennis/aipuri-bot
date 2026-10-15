# -*- coding: utf-8 -*-
# 功能：讀 labels.csv，產生機器人要用的 memes.json（每張圖：編號、台詞、標籤、圖片網址）
import csv
import json
import os

BASE_URL = "https://ozennis.github.io/aipuri-bot/images/"   # 你的圖片網址開頭（結尾要有 /）

memes = []
with open("labels.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        code = (row.get("編號") or "").strip()
        filename = (row.get("檔名") or "").strip()
        # 找不到圖檔就跳過這一列
        if not code or not os.path.exists(os.path.join("images", filename)):
            print("⚠️ 跳過（找不到圖檔）：", code, filename)
            continue
        memes.append({
            "id": code,
            "line": (row.get("台詞") or "").strip(),
            "tags": (row.get("標籤") or "").strip(),
            "url": BASE_URL + filename,
        })

with open("memes.json", "w", encoding="utf-8") as f:
    json.dump(memes, f, ensure_ascii=False, indent=2)

print(f"✅ memes.json 產生完成，共 {len(memes)} 張")