from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, FlexSendMessage, TextSendMessage
)
from google import genai
import re

# LINE API Token และ Channel Secret
CHANNEL_ACCESS_TOKEN = 'Oz6x3Zse8dmKO5HWmiRy3aCa26v1aiRJWAFIcGXp/kvSE58NBWARFg1AUf0beFKgqj/+KavL0VJU6wtGOwc3Zf0UfgnAOLJnEBmUwExf6rbCBPz2wplzFtOUVDxo8HJ7RM7En2r4qYg9eBnQeeeWvQdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'c9810af033f3b71c3575127651aa3045'

# เชื่อมกับ Gemini API
client = genai.Client(api_key="AIzaSyDo2U64Wt4Kwcq7ei1U1TjeTkmmVaaYz1I")

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

app = Flask(__name__)

# สร้างคำตอบจาก Gemini
def generate_answer(question):
    prompt = (
        f"แนะนำเพลงจากคำถามนี้ {question} พร้อมชื่อเพลงและลิงก์ YouTube อย่างน้อย 3 เพลง "
        "ในรูปแบบ: ชื่อเพลง: [ชื่อเพลง] ลิงก์: [ลิงก์ YouTube]"
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )
    return response.text

# สร้าง bubble สำหรับแต่ละเพลง
def create_bubble(title, url):
    video_id = url.split("/")[-1].split("?v=")[-1]
    thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    return {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": thumbnail_url,
            "size": "full",
            "aspectRatio": "16:9",
            "aspectMode": "cover",
            "action": {
                "type": "uri",
                "uri": url
            }
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": title,
                    "weight": "bold",
                    "size": "lg",
                    "wrap": True
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
                        "uri": url
                    }
                }
            ]
        }
    }

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    answer = generate_answer(user_message)

    # แยกชื่อเพลง + ลิงก์ออกมาจากข้อความที่ได้
    matches = re.findall(r'ชื่อเพลง[:\-]?\s*(.+?)\s*ลิงก์[:\-]?\s*(https?://[^\s]+)', answer)

    if not matches:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่พบเพลงในคำตอบ"))
        return

    # สร้าง bubble หลายอัน
    bubbles = [create_bubble(title.strip(), url.strip()) for title, url in matches[:10]]  # จำกัดไม่เกิน 10 เพลง

    carousel = {
        "type": "carousel",
        "contents": bubbles
    }

    flex_message = FlexSendMessage(alt_text="แนะนำเพลงหลายรายการ", contents=carousel)
    line_bot_api.reply_message(event.reply_token, flex_message)

# Webhook URL สำหรับรับข้อความ
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
