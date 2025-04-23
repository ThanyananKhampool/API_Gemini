from google import genai
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage
from flask import Flask, request, abort

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
    prompt = f"คุณคือผู้ให้คำแนะนำ เกี่ยวกับเพลง โดยค้นหาและแนะนำเพลง พร้อมลิ้งyoutubeด้วย ได้ทั้งไทยและสากล {question}"
    response = client.models.generate_content(
        model="gemini-2.0-flash",  # เลือกโมเดลที่ต้องการ
        contents=[prompt]  # ส่งคำถามที่มี prompt ไปยังโมเดล
    )
    return response.text

# ฟังก์ชันจัดการข้อความที่ได้รับจากผู้ใช้
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id  # ได้ User ID ของผู้ใช้

    print(f"Received message: {user_message} from {user_id}")

    # ส่งข้อความที่ผู้ใช้ถามไปยัง Gemini API เพื่อขอคำตอบ
    answer = generate_answer(user_message)
    
    # ส่งคำตอบกลับไปยังผู้ใช้ใน LINE
    response_message = f"คำถาม: {user_message}\nคำตอบ: {answer}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_message))

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