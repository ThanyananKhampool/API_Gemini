from google import genai
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    TextSendMessage, MessageEvent, TextMessage,
    FlexSendMessage
)
from flask import Flask, request, abort
from datetime import datetime
import random

# === LINE API Token และ Secret ===
CHANNEL_ACCESS_TOKEN = 'Oz6x3Zse8dmKO5HWmiRy3aCa26v1aiRJWAFIcGXp/kvSE58NBWARFg1AUf0beFKgqj/+KavL0VJU6wtGOwc3Zf0UfgnAOLJnEBmUwExf6rbCBPz2wplzFtOUVDxo8HJ7RM7En2r4qYg9eBnQeeeWvQdB04t89/1O/w1cDnyilFU='
CHANNEL_SECRET = 'c9810af033f3b71c3575127651aa3045'

# === Gemini API Key ===
client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

# === LINE SDK Setup ===
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# === Flask Setup ===
app = Flask(__name__)

# === Gemini Function ===
def generate_answer(question):
    prompt_th = (
        f"แนะนำเพลง 3 เพลง ที่เหมาะกับคำว่า: '{question}' "
        f"ให้ตอบกลับเป็น format ต่อไปนี้เท่านั้น (ห้ามเขียนอย่างอื่น):\n\n"
        f"เพลง: <ชื่อเพลง>\nเหตุผล: <สั้นๆ 1-2 บรรทัด>\nลิงก์: <ลิงก์ YouTube>\n\n"
        f"ทำแบบนี้ 3 ชุด ห้ามตอบเกิน และห้ามใส่ prefix หรือข้อความอื่นนอกจาก format นี้"
    )
    prompt_en = (
        f"Recommend 3 songs that match the word: '{question}'. "
        f"Reply in the following format only (do not include anything else):\n\n"
        f"Song: <Song Title>\nReason: <Short explanation (1–2 lines)>\nLink: <YouTube Link>\n\n"
        f"Do this for 3 songs only. Do not exceed or include any prefix."
    )
    prompt = prompt_th + "\n\n---\n\n" + prompt_en

    response = client.models.generate_content(
        model="gemini-2.0-pro",
        contents=[prompt]
    )
    return response.text

# === Parse Gemini Response ===
def parse_gemini_response(text):
    songs = []
    for block in text.strip().split("\n\n"):
        lines = block.strip().split("\n")
        if len(lines) >= 3:
            title_line = [l for l in lines if "เพลง:" in l or "Song:" in l]
            desc_line = [l for l in lines if "เหตุผล:" in l or "Reason:" in l]
            url_line = [l for l in lines if "ลิงก์:" in l or "Link:" in l]

            if title_line and desc_line and url_line:
                title = title_line[0].split(":", 1)[1].strip()
                desc = desc_line[0].split(":", 1)[1].strip()
                url = url_line[0].split(":", 1)[1].strip()
                songs.append({"title": title, "desc": desc, "url": url})
    return songs

# === Build Flex Bubble ===
def build_song_bubble(song):
    return {
        "type": "bubble",
        "size": "kilo",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": song["title"],
                    "weight": "bold",
                    "size": "lg",
                    "wrap": True,
                    "color": "#1DB954"
                },
                {
                    "type": "text",
                    "text": song["desc"],
                    "wrap": True,
                    "size": "sm",
                    "color": "#666666"
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "horizontal",
            "contents": [
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "🔗 เปิดใน YouTube",
                        "uri": song["url"]
                    }
                }
            ]
        }
    }

# === Create Carousel ===
def create_carousel_message(answer_text):
    song_list = parse_gemini_response(answer_text)
    bubbles = [build_song_bubble(song) for song in song_list]

    return FlexSendMessage(
        alt_text="แนะนำเพลง",
        contents={
            "type": "carousel",
            "contents": bubbles
        }
    )

# === Handle Message ===
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    user_id = event.source.user_id

    print(f"Received message: {user_message} from {user_id}")

    greetings = ['สวัสดี', 'hello', 'hi', 'หวัดดี', 'เฮลโหล', 'ไง']
    if any(greet in user_message.lower() for greet in greetings):
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_greeting = "สวัสดีตอนเช้าครับ ☀️"
        elif 12 <= hour < 17:
            time_greeting = "สวัสดีตอนบ่ายครับ 🌤"
        elif 17 <= hour < 21:
            time_greeting = "สวัสดีตอนเย็นครับ 🌇"
        else:
            time_greeting = "สวัสดีตอนกลางคืนครับ 🌙"

        intro_options = [
            "ผมคือบอทแนะนำเพลง 🎧",
            "ผมช่วยเลือกเพลงให้เหมาะกับอารมณ์ของคุณได้ครับ 🎶",
            "พิมพ์ความรู้สึกของคุณมา แล้วผมจะหาเพลงให้เองครับ 😊",
            "อยากฟังเพลงแนวไหน บอกผมมาได้เลยครับ 🎼"
        ]
        intro = random.choice(intro_options)

        reply_text = f"{time_greeting}\n{intro}"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        return

    # หากไม่ใช่คำทักทาย → ประมวลผลหาเพลง
    try:
        answer = generate_answer(user_message)
        print("Gemini raw response:\n", answer)

        flex_msg = create_carousel_message(answer)
        line_bot_api.reply_message(event.reply_token, flex_msg)
    except Exception as e:
        print("Error:", e)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ขออภัย บอทไม่สามารถตอบคำถามนี้ได้ในตอนนี้ 😢")
        )

# === Webhook Endpoint ===
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Error in webhook:", e)
        abort(400)

    return 'OK'

# === Main ===
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
