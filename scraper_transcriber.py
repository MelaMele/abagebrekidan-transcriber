import os
import asyncio
import requests
from telethon import TelegramClient
import whisper

# GitHub Secrets ላይ ያስገቧቸውን መረጃዎች ማንበብ
API_ID = int(os.environ.get("TELEGRAM_API_ID"))
API_HASH = os.environ.get("TELEGRAM_API_HASH")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHANNEL_USERNAME = 'abagebrekidan'

# የTelethon Client ማዘጋጀት
client = TelegramClient('bot_session', API_ID, API_HASH)

def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Bot Token ወይም Chat ID አልተገኘም!")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # ረጅም ጽሁፍ ከሆነ ከፋፍሎ ለመላክ
    for i in range(0, len(text), 4000):
        chunk = text[i:i+4000]
        payload = {
            "chat_id": CHAT_ID,
            "text": f"📖 **የአባ ገብረኪዳን ትምህርት (በጽሁፍ)፦**\n\n{chunk}",
            "parse_mode": "Markdown"
        }
        requests.post(url, data=payload)

async def main():
    print("ከቴሌግራም ጋር በBot Token በመገናኘት ላይ...")
    # ቀጥታ በBot Token ማስነሳት (ምንም አይነት የቁጥር/OTP ጥያቄ አይጠይቅም)
    await client.start(bot_token=BOT_TOKEN)
    
    print("Whisper AI (Small model) በመጫን ላይ...")
    model = whisper.load_model("small")
    
    print(f"ከ @{CHANNEL_USERNAME} ቻናል ኦዲዮዎችን በመፈለግ ላይ...")
    
    count = 0
    # ከቻናሉ የመጨረሻዎቹን 10 መልእክቶች መፈተሽ
    async for message in client.iter_messages(CHANNEL_USERNAME, limit=10):
        if message.voice or message.audio:
            count += 1
            print(f"\n[+] የኦዲዮ ፋይል ተገኝቷል (ID: {message.id})...")
            
            # ፋይሉን ማውረድ
            file_path = await message.download_media(file="downloads/")
            print(f"ወርዷል: {file_path}")
            
            print("ወደ አማርኛ ጽሁፍ እየተቀየረ ነው...")
            result = model.transcribe(file_path, language="am")
            extracted_text = result["text"]
            
            if extracted_text.strip():
                print("ጽሁፉን በቴሌግራም ቦት በመላክ ላይ...")
                send_telegram_message(extracted_text)
                print(f"✅ ኦዲዮ ID {message.id} በቦት ተልኳል!")
            else:
                print("⚠️ በድምፁ ውስጥ ምንም ጽሁፍ አልተገኘም።")
                
            # የወረደውን ፋይል ማጽዳት
            if os.path.exists(file_path):
                os.remove(file_path)

    if count == 0:
        print("በመጨረሻዎቹ መልእክቶች ውስጥ ምንም የድምፅ ፋይል አልተገኘም።")
        
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
