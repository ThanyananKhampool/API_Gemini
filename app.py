from google import genai
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage
from flask import Flask, request, abort
import json
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
    prompt = (
        f"แนะนำเพลงที่มีฟีลเหมือนในหนัง coming-of-age หรือคำว่า '{question}' "
        f"จำนวน 3 เพลง ไทยหรือสากลก็ได้ ให้แสดงผลในรูปแบบ JSON เท่านั้น "
        f"รูปแบบ JSON:\n"
        f"[{{\"title\": \"ชื่อเพลง\", \"artist\": \"ศิลปิน\", \"youtube_url\": \"ลิงก์ YouTube\", \"reason\": \"เหตุผลที่เลือกเพลงนี้\"}}, ...]\n"
        f"ตัวอย่าง: "
        f"[{{\"title\": \"Lover\", \"artist\": \"Taylor Swift\", \"youtube_url\": \"https://youtu.be/1i8oYSe2f9c\", \"reason\": \"เพลงนี้เต็มไปด้วยความรักโรแมนติกและเสียงหวานของ Taylor\"}}]"
    )

    response = client.generate_content(
        model="gemini-2.0-flash",
        contents=[{"role": "user", "parts": [prompt]}]
    )
    return response.text

# ฟังก์ชันจัดการข้อความที่ได้รับจากผู้ใช้
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id

    print(f"📨 User message: {user_message} from {user_id}")

    try:
        answer = generate_answer(user_message)
        print("[🧠 Gemini response]:", answer)

        # พยายามแยก JSON ออกมาจากข้อความที่ตอบ
        try:
            json_text = re.search(r"\[.*\]", answer, re.DOTALL).group()
            songs = json.loads(json_text)

            formatted = ""
            for i, song in enumerate(songs, 1):
                formatted += f"{i}. 🎵 {song['title']} - {song['artist']}\n🔗 {song['youtube_url']}\n💡 {song['reason']}\n\n"

            response_message = f"🎧 เพลงที่มีฟีล '{user_message}':\n\n{formatted.strip()}"

        except Exception as e:
            print("⚠️ JSON Decode Error:", e)
            response_message = f"⚠️ ไม่สามารถแปลงข้อมูลจาก AI ได้:\n\n{answer}"

    except Exception as e:
        print("❌ ERROR:", e)
        response_message = f"เกิดข้อผิดพลาด: {e}"

    # ส่งข้อความกลับไปยังผู้ใช้ใน LINE
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=response_message)
    )

# Webhook URL สำหรับรับข้อความจาก LINE
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print("[📩 Callback received]", body)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("❌ Callback error:", e)
        abort(400)

    return 'OK'

# รัน Flask
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

        model="gemini-2.0-flash",
        contents=[{"role": "user", "parts": [prompt]}]
    )
    return response.text

# ฟังก์ชันจัดการข้อความที่ได้รับจากผู้ใช้
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id

    print(f"Received message: {user_message} from {user_id}")

    try:
        answer = generate_answer(user_message)

        try:
            songs = json.loads(answer)
            formatted = ""
            for i, song in enumerate(songs, 1):
                formatted += f"{i}. {song['title']} - {song['artist']}\n{song['youtube_url']}\n💡 {song['reason']}\n\n"
            response_message = f"🎧 แนะนำเพลงสำหรับ '{user_message}' 🎶\n\n{formatted}"
        except json.JSONDecodeError:
            response_message = f"⚠️ ขอโทษครับ ข้อมูลที่ได้จาก AI ไม่อยู่ในรูปแบบ JSON ที่ต้องการ:\n\n{answer}"

    except Exception as e:
        response_message = f"❌ เกิดข้อผิดพลาด: {e}"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message.strip()))

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
