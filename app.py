from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, FlexSendMessage, TextSendMessage
)
from google import genai
import re

# LINE API Access Token และ Channel Secret
CHANNEL_ACCESS_TOKEN = 'Oz6x3Zse8dmKO5HWmiRy3aCa26v1aiRJWAFIcGXp/kvSE58NBWARFg1AUf0beFKgqj/+KavL0VJU6wtGOwc3Zf0UfgnAOLJnEBmUwExf6rbCBPz2wplzFtOUVDxo8HJ7RM7En2r4qYg9eBnQeeeWvQdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'c9810af033f3b71c3575127651aa3045'

# สร้าง client สำหรับเชื่อมต่อกับ Gemini API
client = genai.Client(api_key="AIzaSyDo2U64Wt4Kwcq7ei1U1TjeTkmmVaaYz1I")

# สร้าง LineBotApi และ WebhookHandler
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# สร้าง Flask app
app = Flask(__name__)

# ฟังก์ชันหลักในการใช้ Gemini API
def generate_answer(question):
    prompt = f"คุณคือผู้ให้คำแนะนำเกี่ยวกับเพลง แนะนำเพลงจากคำถามนี้ พร้อมลิงก์ YouTube ด้วย: {question}"
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )
    return response.text

# ฟังก์ชันจัดการข้อความที่ได้รับจากผู้ใช้
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id

    print(f"Received message: {user_message} from {user_id}")

    # ดึงคำตอบจาก Gemini
    answer = generate_answer(user_message)

    # หา YouTube URL
    youtube_links = re.findall(r'(https?://(?:www\.)?youtu(?:\.be|be\.com)/[^\s]+)', answer)
    youtube_url = youtube_links[0] if youtube_links else None

    if youtube_url:
        video_id = youtube_url.split("/")[-1].split("?v=")[-1]
        thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

        flex_message = FlexSendMessage(
            alt_text="แนะนำเพลงจาก Gemini",
            contents={
                "type": "bubble",
                "hero": {
                    "type": "image",
                    "url": thumbnail_url,
                    "size": "full",
                    "aspectRatio": "16:9",
                    "aspectMode": "cover",
                    "action": {
                        "type": "uri",
                        "uri": youtube_url
                    }
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "🎧 เพลงที่แนะนำ",
                            "weight": "bold",
                            "size": "xl"
                        },
                        {
                            "type": "text",
                            "text": user_message,
                            "wrap": True,
                            "color": "#666666",
                            "size": "sm"
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "button",
                            "style": "link",
                            "height": "sm",
                            "action": {
                                "type": "uri",
                                "label": "ฟังบน YouTube",
                                "uri": youtube_url
                            }
                        }
                    ],
                    "flex": 0
                }
            }
        )
        line_bot_api.reply_message(event.reply_token, flex_message)
    else:
        # ถ้าไม่มีลิงก์ YouTube ส่งข้อความปกติ
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ขออภัย ไม่พบลิงก์ YouTube จากคำตอบ"))

# Webhook สำหรับรับข้อความจาก LINE
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Error:", e)
        abort(400)

    return 'OK'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
