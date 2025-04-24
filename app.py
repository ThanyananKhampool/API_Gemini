from google import genai
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage, URIAction, CarouselColumn, CarouselTemplate, TemplateSendMessage
from flask import Flask, request, abort

# LINE API Access Token และ Channel Secret
CHANNEL_ACCESS_TOKEN = 'YOUR_ACCESS_TOKEN'
CHANNEL_SECRET = 'YOUR_CHANNEL_SECRET'

# สร้าง client สำหรับเชื่อมต่อกับ Gemini API
client = genai.Client(api_key="YOUR_API_KEY")

# สร้าง LineBotApi และ WebhookHandler
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# สร้าง Flask app
app = Flask(__name__)

# ฟังก์ชันหลักในการใช้ Gemini API
def generate_answer(question):
    prompt = (
        f"คุณเป็นผู้เชี่ยวชาญในการแนะนำเพลงที่มีความหมายลึกซึ้งและสะท้อนการเติบโตและการค้นหาตัวตน "
        f"ในช่วงเวลาของชีวิตที่เรียกว่า 'coming-of-age' ซึ่งเป็นช่วงที่เราเรียนรู้และเติบโตจากการเผชิญกับ "
        f"อุปสรรคและการค้นพบโลกใหม่ เพลงที่แนะนำต้องสะท้อนอารมณ์ที่เกี่ยวข้องกับการเปลี่ยนแปลงในชีวิต "
        f"การค้นพบตัวเอง หรือความรู้สึกที่เกิดขึ้นเมื่อเราเผชิญกับสถานการณ์สำคัญในชีวิต เช่น การก้าวพ้น "
        f"วัยเด็กไปสู่วัยผู้ใหญ่ หรือการทำความเข้าใจถึงสิ่งที่เราเป็นและสิ่งที่เราต้องการในชีวิต "
        f"แนะนำเพลงที่มีเนื้อหาหรือทำนองที่ช่วยสะท้อนอารมณ์นี้ และเหมาะกับทั้งเพลงไทยและเพลงสากล "
        f"โดยไม่จำเป็นต้องใช้รูปแบบ JSON คำตอบที่ให้สามารถเป็นข้อความธรรมดาและเหมาะสำหรับการตอบกลับใน LINE"
        f"\nโปรดแนะนำ 3 เพลงที่มีฟีล 'coming-of-age' พร้อมกับเหตุผลในการเลือกเพลงเหล่านั้น"
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",  # เลือกโมเดลที่ต้องการ
        contents=[prompt]  # ส่งคำถามที่มี prompt ไปยังโมเดล
    )
    return response.text

# ฟังก์ชันจัดการข้อความที่ได้รับจากผู้ใช้
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id

    print(f"📨 User message: {user_message} from {user_id}")

    try:
        # ส่งคำถามไปยัง Gemini API
        answer = generate_answer(user_message)
        print("[🧠 Gemini response]:", answer)

        # กำหนดเพลงที่แนะนำและลิงค์ YouTube
        song1 = {"title": "เพลง A", "link": "https://www.youtube.com/watch?v=song_link_A", "reason": "สะท้อนการค้นหาตัวตนในวัยรุ่น"}
        song2 = {"title": "เพลง B", "link": "https://www.youtube.com/watch?v=song_link_B", "reason": "พูดถึงการก้าวผ่านความกลัว"}
        song3 = {"title": "เพลง C", "link": "https://www.youtube.com/watch?v=song_link_C", "reason": "เต็มไปด้วยอารมณ์ของการเริ่มต้นใหม่"}

        # สร้าง Carousel Template สำหรับแสดงเพลงพร้อมลิงค์
        carousel_columns = [
            CarouselColumn(
                title=song1['title'],
                text=song1['reason'],
                actions=[URIAction(label="ฟังเพลงนี้", uri=song1['link'])]
            ),
            CarouselColumn(
                title=song2['title'],
                text=song2['reason'],
                actions=[URIAction(label="ฟังเพลงนี้", uri=song2['link'])]
            ),
            CarouselColumn(
                title=song3['title'],
                text=song3['reason'],
                actions=[URIAction(label="ฟังเพลงนี้", uri=song3['link'])]
            )
        ]

        # สร้าง Template ส่งข้อความ Carousel
        carousel_template = CarouselTemplate(columns=carousel_columns)
        template_message = TemplateSendMessage(
            alt_text='เพลงที่แนะนำสำหรับคุณ',
            template=carousel_template
        )

        # ส่งข้อความ Carousel ไปยัง LINE
        line_bot_api.reply_message(
            event.reply_token,
            template_message
        )

    except Exception as e:
        print("❌ ERROR:", e)
        response_message = f"เกิดข้อผิดพลาด: {e}"

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
