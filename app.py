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

# Gemini API Key
GEMINI_API_KEY = 'AIzaSyDo2U64Wt4Kwcq7ei1U1TjeTkmmVaaYz1I'
client = genai.Client(api_key=GEMINI_API_KEY)

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

app = Flask(__name__)

# ฟังก์ชันสร้างคำตอบจาก Gemini
def generate_answer(question):
    prompt = (
        f"แนะนำเพลงจากคำถามนี้: {question} โดยให้ผลลัพธ์เป็น 3 เพลงขึ้นไป "
        "ในรูปแบบ: ชื่อเพลง: [ชื่อเพลง] ศิลปิน: [ชื่อศิลปิน] ลิงก์: [ลิงก์ YouTube]"
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt]
    )
    return response.text

# ฟังก์ชันสร้าง Flex Bubble เพลง
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
                    "color": "#E91E63"
                },
                {
                    "type": "text",
                    "text": f"👤 {artist}",
                    "size": "sm",
                    "color": "#888888",
                    "wrap": True,
                    "action": {
                        "type": "message",
                        "label": "ดูศิลปิน",
                        "text": f"ดูศิลปิน {artist}"
                    }
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
                    "color": "#E91E63",
                    "action": {
                        "type": "uri",
                        "label": "🎧 ฟังเพลง",
                        "uri": url
                    }
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "action": {
                        "type": "uri",
                        "label": "📄 ดูเนื้อเพลง",
                        "uri": f"https://www.google.com/search?q=lyrics+{title}+{artist}"
                    }
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "action": {
                        "type": "message",
                        "label": "➕ เพิ่มใน Playlist",
                        "text": f"เพิ่ม {title} ใน Playlist"
                    }
                },
                {
                    "type": "button",
                    "style": "secondary",
                    "action": {
                        "type": "message",
                        "label": "📤 แชร์เพลงนี้",
                        "text": f"แชร์เพลง {title}"
                    }
                }
            ]
        }
    }

# ฟังก์ชันเมื่อมีข้อความเข้ามา
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    if user_message.startswith("ดูศิลปิน"):
        artist_name = user_message.replace("ดูศิลปิน", "").strip()
        artist_flex = {
            "type": "bubble",
            "hero": {
                "type": "image",
                "url": "https://via.placeholder.com/600x400.png?text=Artist",
                "size": "full",
                "aspectRatio": "20:13",
                "aspectMode": "cover"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": artist_name, "weight": "bold", "size": "xl"},
                    {"type": "text", "text": "🎤 ศิลปินยอดนิยม", "size": "sm", "color": "#888888"},
                    {"type": "text", "text": "ติดตามเพลงเพิ่มเติมใน YouTube หรือ Spotify", "wrap": True, "size": "xs", "color": "#AAAAAA"}
                ]
            }
        }
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(alt_text=f"ข้อมูลศิลปิน {artist_name}", contents=artist_flex)
        )
        return

    answer = generate_answer(user_message)
    matches = re.findall(
        r'ชื่อเพลง[:\-]?\s*(.*?)\s*ศิลปิน[:\-]?\s*(.*?)\s*ลิงก์[:\-]?\s*(https?://[^\s]+)',
        answer
    )

    if not matches:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่พบเพลงในคำตอบ"))
        return

    bubbles = [create_bubble(i + 1, title.strip(), url.strip(), artist.strip()) for i, (title, artist, url) in enumerate(matches[:10])]
    carousel = {"type": "carousel", "contents": bubbles}
    flex_message = FlexSendMessage(alt_text="แนะนำเพลงหลายรายการ", contents=carousel)
    line_bot_api.reply_message(event.reply_token, flex_message)

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
