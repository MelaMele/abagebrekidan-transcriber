import os
import re
import requests
from bs4 import BeautifulSoup
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

def get_real_post_ids():
    """ የቻናሉን ትክክለኛ የቅርብ ጊዜ ፖስት IDዎች ለማግኘት """
    url = f"https://t.me/s/{CHANNEL_USERNAME}?before=999999"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    print(f"[+] ከ {url} የቅርብ ጊዜ ፖስቶችን በመፈለግ ላይ...")
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        post_ids = []
        
        messages = soup.find_all('div', class_='tgme_widget_message')
        for msg in messages:
            data_post = msg.get('data-post')
            if data_post and '/' in data_post:
                try:
                    pid = int(data_post.split('/')[-1])
                    post_ids.append(pid)
                except ValueError:
                    pass
                    
        if not post_ids:
            matches = re.findall(r'data-post="' + CHANNEL_USERNAME + r'/(\d+)"', res.text)
            if matches:
                post_ids = [int(m) for m in matches]
                
        if post_ids:
            max_id = max(post_ids)
            print(f"✅ ትክክለኛው የቅርብ ጊዜ ፖስት ID ተገኝቷል፦ {max_id}")
            # የመጨረሻዎቹን 15 ፖስቶች መውሰድ
            return list(range(max_id, max(1, max_id - 15), -1))
    except Exception as e:
        print(f"⚠️ ስህተት ተከሰተ፦ {e}")
        
    return []

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
    
    check_ids = get_real_post_ids()
    if not check_ids:
        print("⚠️ የሚፈተሹ ፖስቶች አልተገኙም።")
        return
        
    print(f"[+] የሚፈተሹ የፖስት IDዎች፦ {check_ids}")

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
                    send_telegram_message(f"📍 **የፖስት ቁጥር፦** {post_id}\n🔗 {post_url}\n\n" + extracted_text)
                    print(f"✅ ፖስት {post_id} በቦት ተልኳል!")
                else:
                    print("⚠️ በድምፁ ውስጥ ምንም ጽሁፍ አልተገኘም።")
                    
                os.remove(audio_filename)
            else:
                print("ℹ️ በዚህ ፖስት ላይ ኦዲዮ አልተገኘም።")
                
        except Exception:
            print(f"ℹ️ ፖስት {post_id} ኦዲዮ የለውም ወይም የጽሁፍ ፖስት ነው (ይዘለላል)።")

    if found_audio_count == 0:
        print("\n⚠️ በተፈተሹት ፖስቶች ውስጥ ምንም ኦዲዮ አልተገኘም።")

if __name__ == "__main__":
    main()
