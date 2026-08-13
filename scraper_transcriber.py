import os
import glob
import requests
import whisper
import yt_dlp

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHANNEL_URL = "https://t.me/s/abagebrekidan"

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

def download_channel_audios():
    os.makedirs("downloads", exist_ok=True)
    
    # yt-dlp ማዘጋጃ
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'ignoreerrors': True,
        'quiet': False,
        'playlistend': 5, # የመጨረሻዎቹን 5 ኦዲዮዎች ብቻ ለመውሰድ
    }
    
    print("በ yt-dlp አማካኝነት ከአባ ገብረኪዳን ቻናል ኦዲዮዎችን በመፈለግ ላይ...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([CHANNEL_URL])

def main():
    # 1. ኦዲዮዎችን ማውረድ
    download_channel_audios()
    
    # በ downloads ፎልደር ውስጥ የወረዱ ፋይሎችን ማግኘት
    audio_files = glob.glob("downloads/*")
    print(f"\n[+] በጠቅላላ {len(audio_files)} የድምፅ ፋይሎች ወርደዋል።")
    
    if not audio_files:
        print("ምንም የድምፅ ፋይል ማውረድ አልተቻለም።")
        return

    # 2. Whisper AI ሞዴል መጫን
    print("\nWhisper AI (Small model) በመጫን ላይ...")
    model = whisper.load_model("small")
    
    # 3. እያንዳንዱን ኦዲዮ ወደ ጽሁፍ መቀየር
    for idx, audio_file in enumerate(audio_files, start=1):
        print(f"\n[+] ኦዲዮ {idx} ({audio_file}) ወደ አማርኛ ጽሁፍ እየተቀየረ ነው...")
        
        try:
            result = model.transcribe(audio_file, language="am")
            extracted_text = result["text"]
            
            if extracted_text.strip():
                print(f"ጽሁፉን በቴሌግራም ቦት በመላክ ላይ...")
                send_telegram_message(extracted_text)
                print(f"✅ ኦዲዮ {idx} በቦት ተልኳል!")
            else:
                print(f"⚠️ በኦዲዮ {idx} ውስጥ ምንም ድምፅ አልተገኘም።")
                
        except Exception as e:
            print(f"❌ ስህተት ተከሰተ፦ {e}")
            
        # የወረደውን ፋይል ማጽዳት
        if os.path.exists(audio_file):
            os.remove(audio_file)

if __name__ == "__main__":
    main()
