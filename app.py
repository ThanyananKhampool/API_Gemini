import re
from linebot.models import (
    MessageEvent, TextMessage, FlexSendMessage, TextSendMessage
)
from google import genai

# ฟังก์ชันสร้างคำตอบจาก Gemini
def generate_answer(question):
    prompt = f"แนะนำเพลงจากคำถามนี้: {question} โดยให้ผลลัพธ์เป็น 3 เพลงขึ้นไป ในรูปแบบ: ชื่อเพลง: [ชื่อเพลง] ศิลปิน: [ชื่อศิลปิน] ลิงก์: [ลิงก์ YouTube]"
    response = client.models.generate_content(
        model="gemini-2.0-flash",  # เลือกโมเดลที่ต้องการ
        contents=[prompt]  # ส่งคำถามที่มี prompt ไปยังโมเดล
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

    # ตรวจสอบการรับคำตอบจาก Gemini
    answer = generate_answer(user_message)
    matches = re.findall(
        r'ชื่อเพลง[:\\-]?\\s*(.*?)\\s*ศิลปิน[:\\-]?\\s*(.*?)\\s*ลิงก์[:\\-]?\\s*(https?://[^\\s]+)', 
        answer
    )

    if not matches:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่พบเพลงในคำตอบ"))
        return

    # สร้าง Bubble สำหรับเพลงที่ได้จาก Gemini
    bubbles = [
        create_bubble(i + 1, title.strip(), url.strip(), artist.strip())
        for i, (title, artist, url) in enumerate(matches[:10])
    ]
    carousel = {"type": "carousel", "contents": bubbles}

    # ส่ง Flex Message กลับไปยังผู้ใช้
    flex_message = FlexSendMessage(alt_text="แนะนำเพลงหลายรายการ", contents=carousel)
    line_bot_api.reply_message(event.reply_token, flex_message)
