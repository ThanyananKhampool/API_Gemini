from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    TextMessage, MessageEvent, FlexSendMessage,
    BubbleContainer, BoxComponent, TextComponent,
    URIAction, ButtonComponent
)
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

# ฟังก์ชันหลักในการใช้ Gemini API เพื่อสร้างข้อความแนะนำเพลงในรูปแบบกล่องโปรโมชัน
def generate_answer(question):
    prompt = f"""
คุณคือผู้ช่วยแนะนำเพลงที่ตอบเป็นข้อความโปรโมชันแบบสดใส เช่นร้านค้าแฟชั่น
- ตอบแบบใส่อิโมจิ 🎵🔥❤️✨
- มีหัวข้อชัดเจน เช่น 🎧 เพลงแนะนำวันนี้ 🎧
- แนะนำเพลง 2-3 เพลง พร้อมลิงก์ YouTube
- เป็นเพลงไทยหรือสากลก็ได้
- ตอบแบบน่ารัก สดใส กระตุ้นให้อยากฟังเพลง
- เหมาะสำหรับส่งใน LINE

คำถามจากผู้ใช้: {question}
กรุณาสร้างคำตอบในรูปแบบกล่องโปรโมชัน
"""
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )
    return response.text

# ฟังก์ชันแปลงข้อความที่ได้จาก Gemini ให้กลายเป็น Flex Message
def create_flex_message(answer_text):
    lines = answer_text.strip().split("\n")[1:]  # ข้ามบรรทัดแรกหัวข้อ
    contents = []

    for line in lines:
        if "👉" in line:
            title, link = line.split("👉")
            contents.append(
                BoxComponent(
                    layout="horizontal",
                    contents=[
                        TextComponent(text=title.strip(), size="sm", wrap=True, flex=3),
                        ButtonComponent(
                            style="link",
                            height="sm",
                            action=URIAction(label="ฟังเลย", uri=link.strip()),
                            flex=1
                        )
                    ],
                    spacing="md",
                    margin="md"
                )
            )

    bubble = BubbleContainer(
        body=BoxComponent(
            layout="vertical",
            contents=[
                TextComponent(text="🎧 เพลงแนะนำวันนี้ 🎧", weight="bold", size="md", color="#1DB954"),
                *contents
            ]
        )
    )
    return FlexSendMessage(alt_text="แนะนำเพลงมาแล้วจ้า~", contents=bubble)

# ฟังก์ชันจัดการข้อความจากผู้ใช้ LINE
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id  # ใช้ได้กรณีอยากเก็บ user_id

    print(f"Received message: {user_message} from {user_id}")

    # ส่งคำถามไปยัง Gemini เพื่อขอคำตอบ
    answer = generate_answer(user_message)

    # ตอบกลับด้วย Flex Message
    flex_msg = create_flex_message(answer)

    line_bot_api.reply_message(
        event.reply_token,
        flex_msg
    )

# Webhook endpoint
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

# รันแอป
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
