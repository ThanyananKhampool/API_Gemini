from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    TemplateSendMessage, CarouselTemplate, CarouselColumn, URITemplateAction
)
import json
import re
from google import genai

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

# แปลง YouTube URL เป็น Thumbnail
def extract_youtube_thumbnail(url):
    match = re.search(r"(?:v=|be/)([\w-]+)", url)
    if match:
        video_id = match.group(1)
        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    return "https://i.imgur.com/E8KZ2sT.png"  # fallback image

# ฟังก์ชันหลักในการใช้ Gemini API
def generate_answer(question):
    prompt = f"""แนะนำเพลงที่ตรงกับคำถามนี้: "{question}" 
ให้ผลลัพธ์เป็น JSON list ที่ประกอบด้วย title (ชื่อเพลง) และ url (ลิงก์ YouTube) เท่านั้น เช่น:
[
  {{"title": "เพลงชื่ออะไร", "url": "https://youtube.com/xxx"}},
  {{"title": "ชื่อเพลงสอง", "url": "https://youtube.com/yyy"}}
]"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )

    try:
        songs = json.loads(response.text)
    except Exception as e:
        print("Error parsing JSON from Gemini:", e)
        return []

    return songs

# ฟังก์ชันจัดการข้อความที่ได้รับจากผู้ใช้
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    songs = generate_answer(user_message)

    if not songs:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ขออภัย ไม่สามารถแนะนำเพลงได้ในขณะนี้")
        )
        return

    columns = []
    for song in songs[:10]:  # LINE Carousel จำกัด 10 columns
        thumbnail = extract_youtube_thumbnail(song["url"])
        columns.append(CarouselColumn(
            thumbnail_image_url=thumbnail,
            title=song["title"][:40],  # LINE จำกัด title 40 ตัวอักษร
            text="คลิกเพื่อฟังบน YouTube",
            actions=[URITemplateAction(label="ฟังเพลง", uri=song["url"])]
        ))

    carousel_template = CarouselTemplate(columns=columns)
    message = TemplateSendMessage(
        alt_text='แนะนำเพลงตามคำถามของคุณ',
        template=carousel_template
    )

    line_bot_api.reply_message(event.reply_token, message)

# Webhook URL สำหรับรับข้อความจาก LINE
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
