# -*- coding: utf-8 -*-
"""
《祕密的偶像公主》梗圖 LINE 機器人
功能：
  1. 輸入編號（例如 01-005）→ 回傳那張圖
  2. 輸入「抽」→ 隨機回傳一張圖
  3. 輸入台詞或關鍵字 → 找到 1 張就直接回圖；找到很多張就回最像的＋其他候選編號
  4. 在群組裡：要在關鍵字前面加 #（例如 #好耶）才會搜尋
"""
import os
import re
import json
import random
import unicodedata

from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, ReplyMessageRequest,
    TextMessage, ImageMessage, QuickReply, QuickReplyItem, MessageAction,
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# ===== 1. 讀取鑰匙（電腦上從 .env 讀，雲端上從環境變數讀）=====
load_dotenv()
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    print("⚠️ 找不到 LINE 金鑰！請檢查 .env 檔或雲端的環境變數設定。")

app = Flask(__name__)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# ===== 2. 讀取梗圖資料庫 memes.json =====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "memes.json"), encoding="utf-8") as f:
    MEMES = json.load(f)
MEME_BY_ID = {m["id"]: m for m in MEMES}
print(f"✅ 已載入 {len(MEMES)} 張梗圖")

# ===== 3. 可以自己改的設定 =====
RANDOM_WORDS = {"抽", "隨機", "random", "來一張"}   # 觸發隨機抽圖的字
HELP_WORDS = {"說明", "help", "幫助", "?", "？"}    # 觸發使用說明的字
ID_PATTERN = re.compile(r"^\d{2}-\d{3}$")            # 編號格式：01-005
MAX_LIST = 12                                        # 候選清單最多列幾個
HELP_TEXT = (
    "✨ 祕密的偶像公主梗圖機 ✨\n"
    "・輸入台詞或關鍵字：例如「開心」\n"
    "・輸入「抽」：隨機來一張\n"
    "・輸入編號：例如 01-005\n"
    "・在群組裡：關鍵字前面加 #，例如 #開心"
)


def normalize(text):
    """把文字洗乾淨再比對：全形轉半形、英文轉小寫、去掉空白和標點"""
    text = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"[\W_]+", "", text)


for m in MEMES:
    m["_line"] = normalize(m.get("line", ""))
    m["_key"] = m["_line"] + "|" + normalize(m.get("tags", ""))


def search(keyword):
    """找出台詞或標籤含有關鍵字的圖；台詞完全一樣的排最前面"""
    kw = normalize(keyword)
    if not kw:
        return []
    exact = [m for m in MEMES if m["_line"] == kw]
    partial = [m for m in MEMES if kw in m["_key"] and m["_line"] != kw]
    return exact + partial


def make_quick_reply(ids=None):
    """圖片下方的小按鈕：『再抽一張』＋候選編號（最多 13 顆）"""
    items = [QuickReplyItem(action=MessageAction(label="🎲 再抽一張", text="抽"))]
    for meme_id in (ids or [])[:12]:
        items.append(QuickReplyItem(action=MessageAction(label=meme_id, text=meme_id)))
    return QuickReply(items=items)


def image_msg(meme, quick_reply=None):
    """做出一則圖片訊息"""
    return ImageMessage(
        original_content_url=meme["url"],
        preview_image_url=meme["url"],
        quick_reply=quick_reply,
    )


# ===== 4. 網址路徑 =====
@app.route("/", methods=["GET"])
def home():
    return "祕密的偶像公主梗圖機器人運作中 ✨"


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ 簽章錯誤：Channel secret 可能貼錯了")
        abort(400)
    return "OK"


# ===== 5. 收到文字訊息時要做的事 =====
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    text = event.message.text.strip()
    in_group = event.source.type in ("group", "room")
    messages = []

    if text.lower() in HELP_WORDS:
        messages = [TextMessage(text=HELP_TEXT, quick_reply=make_quick_reply())]

    elif text.lower() in RANDOM_WORDS:
        if MEMES:
            meme = random.choice(MEMES)
            caption = f"【{meme['id']}】{meme.get('line') or '（無台詞）'}"
            messages = [TextMessage(text=caption), image_msg(meme, make_quick_reply())]

    elif ID_PATTERN.match(text):
        meme = MEME_BY_ID.get(text)
        if meme:
            messages = [image_msg(meme, make_quick_reply())]
        elif not in_group:
            messages = [TextMessage(text=f"找不到編號 {text} 的圖喔")]

    else:
        if in_group:
            if not text.startswith(("#", "＃")):
                return
            text = text[1:]
        results = search(text)

        if len(results) == 1:
            messages = [image_msg(results[0], make_quick_reply())]
        elif len(results) > 1:
            others = results[1:MAX_LIST + 1]
            listing = "\n".join(f"【{m['id']}】{m.get('line', '')}" for m in others)
            remain = len(results) - 1 - len(others)
            more = f"\n…還有 {remain} 張，關鍵字打長一點會更準" if remain > 0 else ""
            messages = [
                image_msg(results[0]),
                TextMessage(
                    text=f"找到 {len(results)} 張，先給你最像的！\n其他候選（點按鈕或輸入編號）：\n{listing}{more}",
                    quick_reply=make_quick_reply([m["id"] for m in others]),
                ),
            ]
        elif not in_group:
            messages = [TextMessage(
                text="找不到這句台詞 😢\n試試短一點的關鍵字，或輸入「抽」隨機來一張！",
                quick_reply=make_quick_reply(),
            )]

    if not messages:
        return

    try:
        with ApiClient(configuration) as api_client:
            MessagingApi(api_client).reply_message(
                ReplyMessageRequest(reply_token=event.reply_token, messages=messages)
            )
    except Exception as e:
        print("❌ 回覆失敗：", e)


# ===== 6. 在自己電腦上執行時用的入口 =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)