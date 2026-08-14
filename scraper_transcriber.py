import os
import requests
import yt_dlp
import whisper

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

def get_latest_post_id():
    """የቻናሉን የቅርብ ጊዜ ፖስት ቁጥር ለማወቅ"""
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    import re
    matches = re.findall(r'data-post="' + CHANNEL_USERNAME + r'/(\d+)"', res.text)
    if matches:
        return max(map(int, matches))
    return 500  # ברירת מחדל / Default

def download_audio(post_url, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([post_url])

def main():
    os.makedirs("downloads", exist_ok=True)
    
    latest_id = get_latest_post_id()
    print(f"[+] የቅርብ ጊዜ የፖስት ID፦ {latest_id}")
    
    # የመጨረሻዎቹን 10 ፖስቶች መፈተሽ (ከቅርብ ወደ ኋላ)
    check_ids = list(range(latest_id, max(1, latest_id - 10), -1))
    print(f"[+] የሚፈተሹ ፖስቶች ቁጥር፦ {check_ids}")

    print("\nWhisper AI (Small model) በመጫን ላይ...")
    model = whisper.load_model("small")
    
    found_audio_count = 0
    
    for post_id in check_ids:
        post_url = f"https://t.me/{CHANNEL_USERNAME}/{post_id}"
        audio_filename = f"downloads/audio_{post_id}.mp3"
        
        print(f"\n--------------------------------------------------")
        print(f"[+] ፖስት ID {post_id} በመፈተሽ ላይ፦ {post_url}")
        
        try:
            download_audio(post_url, audio_filename)
            
            if os.path.exists(audio_filename):
                found_audio_count += 1
                print("✅ የድምፅ ፋይል ተገኝቷል! ወደ አማርኛ ጽሁፍ እየተቀየረ ነው...")
                result = model.transcribe(audio_filename, language="am")
                extracted_text = result["text"]
                
                if extracted_text.strip():
                    print("ጽሁፉን በቴሌግራም ቦት በመላክ ላይ...")
                    send_telegram_message(f"📍 **ፖስት ሊንክ:** {post_url}\n\n" + extracted_text)
                    print(f"✅ ፖስት {post_id} በቦት ተልኳል!")
                else:
                    print("⚠️ በድምፁ ውስጥ ምንም ጽሁፍ አልተገኘም።")
                    
                os.remove(audio_filename)
            else:
                print("ℹ️ በዚህ ፖስት ላይ ኦዲዮ አልተገኘም።")
                
        except Exception:
            print(f"ℹ️ ፖስት {post_id} ኦዲዮ የለውም ወይም የጽሁፍ ፖስት ነው (ይዘለላል)።")

    if found_audio_count == 0:
        print("\n⚠️ በተፈተሹት 10 ፖስቶች ውስጥ ምንም ኦዲዮ አልተገኘም።")

if __name__ == "__main__":
    main()
