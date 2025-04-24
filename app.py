from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage, MessageEvent, TextMessage, FlexSendMessage
from flask import Flask, request, abort
from google import genai

# LINE API Access Token และ Channel Secret
CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'
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
    prompt = f"คุณคือผู้ให้คำแนะนำ เกี่ยวกับเพลง โดยค้นหาและแนะนำเพลง พร้อมลิ้งyoutubeด้วย ได้ทั้งไทยและสากล {question}"
    response = client.models.generate_content(
        model="gemini-2.0-flash",  # เลือกโมเดลที่ต้องการ
        contents=[prompt]  # ส่งคำถามที่มี prompt ไปยังโมเดล
    )
    return response.text

# ฟังก์ชันสำหรับการสร้าง Flex Bubble ที่แสดงเพลง
def create_bubble(index, title, url, artist=None):
    video_id = url.split("/")[-1].split("?v=")[-1]
    thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

    return {
        "type": "bubble",
        "size": "mega",
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
            "spacing": "sm",
            "contents": [
                {
                    "type": "text",
                    "text": f"#{index} {title}",
                    "weight": "bold",
                    "size": "xl",
                    "wrap": True,
                    "color": "#E91E63"  # สีชมพู
                },
                {
                    "type": "text",
                    "text": f"ศิลปิน: {artist}",
                    "size": "sm",
                    "color": "#888888",
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
                    "style": "primary",
                    "color": "#E91E63",  # สีชมพู
                    "action": {
                        "type": "uri",
                        "label": "ฟังเพลง",
                        "uri": url
                    }
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "action": {
                        "type": "uri",
                        "label": "ดูเนื้อเพลง",
                        "uri": f"https://www.google.com/search?q=lyrics+{title}+{artist}"
                    }
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "action": {
                        "type": "message",
                        "label": "เพิ่มใน Playlist",
                        "text": f"เพิ่ม {title} ใน Playlist"
                    }
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "action": {
                        "type": "message",
                        "label": "แชร์เพลงนี้",
                        "text": f"แชร์เพลง {title}"
                    }
                }
            ]
        }
    }

# ฟังก์ชันจัดการข้อความที่ได้รับจากผู้ใช้
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    user_id = event.source.user_id  # ได้ User ID ของผู้ใช้

    print(f"Received message: {user_message} from {user_id}")

    # ส่งข้อความที่ผู้ใช้ถามไปยัง Gemini API เพื่อขอคำตอบ
    answer = generate_answer(user_message)
    
    # สมมติว่าได้รับข้อมูลเพลงจากคำตอบของ Gemini API
    # ตัวอย่างข้อมูลเพลง (ในทางปฏิบัติจะดึงข้อมูลจาก Gemini API)
    songs = [
        {"title": "ถ้าเธอรักใครคนหนึ่ง", "artist": "Ink Waruntorn", "url": "https://www.youtube.com/watch?v=fGqMMW57EaM"},
        {"title": "ก่อนฤดูฝน", "artist": "The TOYS", "url": "https://www.youtube.com/watch?v=Gj-zGC-X4j0"},
        {"title": "ภาวนา", "artist": "MEAN", "url": "https://www.youtube.com/watch?v=w4y7eQ59_Kk"}
    ]
    
    # สร้าง Flex Bubble สำหรับแสดงข้อมูลเพลงที่ได้รับ
    bubbles = [create_bubble(i + 1, song["title"], song["url"], song["artist"]) for i, song in enumerate(songs)]

    # ส่ง Flex Message ไปยัง LINE
    flex_message = FlexSendMessage(
        alt_text="เพลงที่แนะนำ",
        contents={
            "type": "carousel",
            "contents": bubbles
        }
    )
    
    line_bot_api.reply_message(event.reply_token, flex_message)

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
