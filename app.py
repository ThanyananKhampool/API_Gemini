from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import *
from google import genai
import json

# LINE API Credentials
CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'
CHANNEL_SECRET = 'YOUR_CHANNEL_SECRET'

# Gemini API Key
GENAI_API_KEY = 'YOUR_GEMINI_API_KEY'

# สร้าง Flask app
app = Flask(__name__)

# LINE API
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Gemini API client
genai.configure(api_key=GENAI_API_KEY)
client = genai.GenerativeModel("gemini-pro")

# ฟังก์ชันเรียก Gemini API
def generate_answer(question):
    prompt = f"""
คุณคือผู้ช่วยแนะนำเพลง ห้ามพูดคุยหรืออธิบาย
ตอบกลับเฉพาะในรูปแบบ JSON เท่านั้น
ตัวอย่าง:
[
  {{
    "title": "Someone Like You - Adele",
    "url": "https://www.youtube.com/watch?v=hLQl3WQQoQ0"
  }},
  {{
    "title": "Let Her Go - Passenger",
    "url": "https://www.youtube.com/watch?v=RBumgq5yVrA"
  }}
]

คำถาม: {question}
"""
    response = client.generate_content(prompt)
    print("🧠 Gemini raw response:\n", response.text)
    return response.text

# ฟังก์ชันรับข้อความจากผู้ใช้
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    response_text = generate_answer(user_message)

    try:
        songs = json.loads(response_text)

        columns = []
        for song in songs[:10]:  # จำกัดสูงสุด 10 กล่อง
            title = song.get("title", "ไม่ทราบชื่อ")[:40]
            url = song.get("url", "#")
            video_id = url.split("v=")[-1][:11]
            thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

            columns.append(
                CarouselColumn(
                    thumbnail_image_url=thumbnail,
                    title=title,
                    text="คลิกเพื่อฟังบน YouTube",
                    actions=[URIAction(label="ฟังเพลง", uri=url)]
                )
            )

        message = TemplateSendMessage(
            alt_text="แนะนำเพลงที่คุณอาจชอบ",
            template=CarouselTemplate(columns=columns)
        )

    except Exception as e:
        print("⚠️ JSON parse error:", e)
        message = TextSendMessage(text="❌ ไม่สามารถแสดงกล่องเพลงได้\nGemini ตอบว่า:\n" + response_text)

    line_bot_api.reply

