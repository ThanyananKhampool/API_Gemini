from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, CarouselTemplate, CarouselColumn, URITemplateAction
)
import json
import re
from google import genai

# LINE API Key และ Gemini API Key
CHANNEL_ACCESS_TOKEN = 'Oz6x3Zse8dmKO5HWmiRy3aCa26v1aiRJWAFIcGXp/kvSE58NBWARFg1AUf0beFKgqj/+KavL0VJU6wtGOwc3Zf0UfgnAOLJnEBmUwExf6rbCBPz2wplzFtOUVDxo8HJ7RM7En2r4qYg9eBnQeeeWvQdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'c9810af033f3b71c3575127651aa3045'
GEMINI_API_KEY = "AIzaSyDo2U64Wt4Kwcq7ei1U1TjeTkmmVaaYz1I"

# Initial setup
client = genai.Client(api_key=GEMINI_API_KEY)
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
app = Flask(__name__)

# แปลง YouTube URL เป็นภาพ Thumbnail
def extract_youtube_thumbnail(url):
    match = re.search(r"(?:v=|be/)([\w-]+)", url)
    if match:
        video_id = match.group(1)
        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    return "https://i.imgur.com/E8KZ2sT.png"  # fallback image

# เรียก Gemini เพื่อขอแนะนำเพลงเป็น JSON
def generate_answer(question):
    prompt = f"""
คุณคือผู้เชี่ยวชาญในการแนะนำเพลงจากคำถามของผู้ใช้
คำถาม: "{question}"

แนะนำเพลงมา 5 เพลง โดยให้ตอบกลับในรูปแบบ JSON ที่มีเฉพาะ:
- "title": ชื่อเพลง
- "url": ลิงก์ YouTube

ห้ามใส่คำอธิบายเพิ่มเติม ห้ามมีหัวข้อ ห้ามพูดคุย ตอบกลับ JSON เท่านั้น

ตัวอย่าง:
[
  {{"title": "Shape of You", "url": "https://youtube.com/watch?v=JGwWNGJdvx8"}},
  {{"title": "Lover", "url": "https://youtube.com/watch?v=-BjZmE2gtdo"}}
]
"""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )

    # Debug: แสดงข้อความดิบจาก Gemini
    print("🧠 Gemini raw response:\n", response.text)

    try:
        songs = json.loads(response.text)
        return songs
    except Exception as e:
        print("⚠️ JSON parsing error:", e)
        return []

# จัดการข้อความจากผู้ใช้ LINE
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    songs = generate_answer(user_message)

    if not songs:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ขออภัย ไม่สามารถแนะนำเพลงได้ในขณะนี้ 😢")
        )
        return

    # สร้าง CarouselTemplate จากเพลง
    columns = []
    for song in songs[:10]:  # สูงสุด 10 กล่อง
        thumbnail = extract_youtube_thumbnail(song["url"])
        columns.append(CarouselColumn(
            thumbnail_image_url=thumbnail,
            title=song["title"][:40],
            text="คลิกเพื่อฟังบน YouTube",
            actions=[URITemplateAction(label="ฟังเพลง", uri=song["url"])]
        ))

    carousel_template = CarouselTemplate(columns=columns)
    message = TemplateSendMessage(
        alt_text='🎵 แนะนำเพลงที่คุณอาจชอบ',
        template=carousel_template
    )

    line_bot_api.reply_message(event.reply_token, message)

# Webhook สำหรับ LINE
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("❌ LINE handler error:", e)
        abort(400)

    return 'OK'

# Run app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
