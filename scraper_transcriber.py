import os
import asyncio
import requests
import re
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession
from faster_whisper import WhisperModel

# Environment Variables
API_ID = int(os.environ.get("TELEGRAM_API_ID", 0))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "").strip().strip('"').strip("'")
STRING_SESSION = os.environ.get("TELEGRAM_STRING_SESSION", "").strip().strip('"').strip("'")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip().strip('"').strip("'")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip().strip('"').strip("'")
CHANNEL_USERNAME = "abagebrekidan"

def clean_hallucinations(text):
    """የማይፈለጉ የእብሪት/የመደጋገም ፊደላትንና ነጥቦችን ያፀዳል"""
    if not text:
        return ""
    
    # ተደጋጋሚ ነጥቦችን፣ ሰረዞችንና ኮማዎችን ማስወገድ
    text = re.sub(r'[\.]{2,}', '። ', text)
    text = re.sub(r'[\,]{2,}', '፣ ', text)
    text = re.sub(r'([፣፤።\?\s])\1{2,}', r'\1', text)
    
    # አማርኛ ፊደላት፣ ቁጥሮች እና መሰረታዊ ስርዓተ-ነጥቦች ብቻ እንዲቀሩ
    cleaned_chars = []
    for char in text:
        if re.match(r'[\u1200-\u137F0-9\s\.\,\:\!\?\-\"\'፣፤።፦\(\)]', char):
            cleaned_chars.append(char)
            
    cleaned_text = "".join(cleaned_chars)
    return re.sub(r'\s+', ' ', cleaned_text).strip()

def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ Bot Token ወይም Chat ID አልተገኘም!")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # ቴሌግራም ከ 4000 ፊደል በላይ አይቀበልም፤ በክፍል በክፍል መላክ
    for i in range(0, len(text), 4000):
        chunk = text[i:i+4000]
        payload = {
            "chat_id": CHAT_ID,
            "text": chunk,
            "disable_web_page_preview": True
        }
        try:
            res = requests.post(url, data=payload)
            if res.status_code != 200:
                print(f"⚠️ መልዕክት መላክ አልተቻለም፦ {res.text}")
        except Exception as e:
            print(f"❌ ስህተት፦ {e}")

async def main():
    print(f"✅ የተገኘው STRING_SESSION ርዝመት፦ {len(STRING_SESSION)} ፊደላት")
    
    os.makedirs("downloads", exist_ok=True)
    print("[+] ከቴሌግራም ሰርቨር ጋር በመገናኘት ላይ...")

    async with TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH) as client:
        print(f"✅ ከ @{CHANNEL_USERNAME} የቅርብ ጊዜ ፖስቶችን በመፈለግ ላይ...")
        messages = await client.get_messages(CHANNEL_USERNAME, limit=10)

        # ባለፉት 7 ሰዓታት ውስጥ የተፖሰቱትን ብቻ መምረጥ
        now = datetime.now(timezone.utc)
        time_threshold = now - timedelta(hours=7)

        audio_messages = []
        for msg in messages:
            is_audio = msg.voice or msg.audio or (msg.document and msg.document.mime_type and msg.document.mime_type.startswith('audio/'))
            if is_audio and msg.date > time_threshold:
                audio_messages.append(msg)

        print(f"✅ ባለፉት 7 ሰዓታት ውስጥ የተፖሰቱ {len(audio_messages)} አዲስ የድምፅ ፖስቶች ተገኝተዋል!")
        if not audio_messages:
            print("ℹ️ ምንም አዲስ የድምፅ ፖስት አልተገኘም።")
            return

        print("\nWhisper AI (Faster-Whisper large-v3-turbo) በመጫን ላይ...")
        # CPU ላይ በፍጥነት እንዲሰራ int8 ተጠቅመናል
        model = WhisperModel("deepdml/faster-whisper-large-v3-turbo-ct2", device="cpu", compute_type="int8")

        for msg in reversed(audio_messages):
            file_path = f"downloads/audio_{msg.id}.mp3"
            print(f"\n[+] የድምፅ ፖስት ID {msg.id} በማውረድ ላይ...")

            await client.download_media(msg, file=file_path)

            if os.path.exists(file_path):
                print(f"ወደ አማርኛ ጽሁፍ እየተቀየረ ነው (ID: {msg.id})...")
                
                try:
                    # vad_filter=True ጸጥታዎችን ቆርጦ ስለሚጥል ነጥብ ነጥብ (... ...) የሚመጣውን ያጠፋል
                    segments, _ = model.transcribe(
                        file_path,
                        language="am",
                        task="transcribe",
                        beam_size=5,
                        vad_filter=True,
                        vad_parameters=dict(min_silence_duration_ms=500),
                        initial_prompt="ይህ በአማርኛ ቋንቋ የተሰጠ የኢትዮጵያ ኦርቶዶክስ ተዋሕዶ ቤተክርስቲያን ስብከትና ትምህርት ነው።"
                    )

                    transcribed_text = " ".join([seg.text for seg in segments])
                    clean_text = clean_hallucinations(transcribed_text)

                    if clean_text and len(clean_text) > 15:
                        post_url = f"https://t.me/{CHANNEL_USERNAME}/{msg.id}"
                        full_message = f"📖 የአባ ገብረኪዳን ትምህርት (በጽሁፍ)፦\n\n📍 የፖስት ቁጥር፦ {msg.id}\n🔗 {post_url}\n\n{clean_text}"
                        send_telegram_message(full_message)
                        print(f"✅ ፖስት {msg.id} በተሳካ ሁኔታ በፅሁፍ ተልኳል!")
                    else:
                        print(f"⚠️ ፖስት {msg.id} ተገቢ የሆነ የአማርኛ ድምፅ ስላልተገኘበት ተዘልሏል።")

                except Exception as e:
                    print(f"❌ Transcribe ሲደረግ ስህተት ተፈጠረ፦ {e}")

                # ፋይሉን ማጽዳት
                if os.path.exists(file_path):
                    os.remove(file_path)

if __name__ == "__main__":
    asyncio.run(main())
