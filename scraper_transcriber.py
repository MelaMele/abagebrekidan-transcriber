import os
import asyncio
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession
import whisper

API_ID = int(os.environ.get("TELEGRAM_API_ID", 0))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
STRING_SESSION = os.environ.get("TELEGRAM_STRING_SESSION")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHANNEL_USERNAME = "abagebrekidan"

def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Bot Token ወይም Chat ID አልተገኘም!")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    for i in range(0, len(text), 4000):
        chunk = text[i:i+4000]
        payload = {
            "chat_id": CHAT_ID,
            "text": f"📖 **የአባ ገብረኪዳን ትምህርት (በጽሁፍ)፦**\n\n{chunk}",
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, data=payload)
        except Exception as e:
            print(f"መልእክት በመላክ ላይ ስህተት ተከሰተ፦ {e}")

async def main():
    if not API_ID or not API_HASH or not STRING_SESSION:
        print("❌ TELEGRAM_API_ID, TELEGRAM_API_HASH ወይም TELEGRAM_STRING_SESSION አልተገኘም!")
        return

    os.makedirs("downloads", exist_ok=True)
    
    print("[+] የቴሌግራም ክላየንት በመክፈት ላይ...")
    async with TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH) as client:
        print(f"[+] ከ @{CHANNEL_USERNAME} የቅርብ ጊዜ መልእክቶችን በመፈለግ ላይ...")
        
        # የቅርብ ጊዜ 20 መልእክቶችን ማውጣት
        messages = await client.get_messages(CHANNEL_USERNAME, limit=20)
        
        # ኦዲዮ፣ ድምፅ (Voice) ወይም MP3 ሰነድ ያላቸውን ብቻ መለየት
        audio_messages = [
            msg for msg in messages 
            if msg.voice or msg.audio or (msg.document and msg.document.mime_type and msg.document.mime_type.startswith('audio/'))
        ]
        
        print(f"✅ በጠቅላላ {len(audio_messages)} የድምፅ መልእክቶች ተገኝተዋል!")
        
        if not audio_messages:
            print("⚠️ በተፈተሹት መልእክቶች ውስጥ ምንም የድምፅ ፖስት አልተገኘም።")
            return

        print("\nWhisper AI (Small model) በመጫን ላይ...")
        model = whisper.load_model("small")
        
        for idx, msg in enumerate(audio_messages, start=1):
            file_path = f"downloads/audio_{msg.id}.mp3"
            print(f"\n--------------------------------------------------")
            print(f"[+] የድምፅ ፖስት ID {msg.id} በማውረድ ላይ...")
            
            await client.download_media(msg, file=file_path)
            
            if os.path.exists(file_path):
                print("ወደ አማርኛ ጽሁፍ እየተቀየረ ነው...")
                result = model.transcribe(file_path, language="am")
                extracted_text = result.get("text", "")
                
                if extracted_text.strip():
                    print("ጽሁፉን በቴሌግራም ቦት በመላክ ላይ...")
                    post_url = f"https://t.me/{CHANNEL_USERNAME}/{msg.id}"
                    send_telegram_message(f"📍 **የፖስት ቁጥር፦** {msg.id}\n🔗 {post_url}\n\n" + extracted_text)
                    print(f"✅ ፖስት {msg.id} በቦት ተልኳል!")
                else:
                    print("⚠️ በድምፁ ውስጥ ምንም ጽሁፍ አልተገኘም።")
                    
                os.remove(file_path)
            else:
                print("⚠️ ፋይሉን ማውረድ አልተቻለም።")

if __name__ == "__main__":
    asyncio.run(main())
