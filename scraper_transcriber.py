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

def get_channel_posts_via_ytdlp():
    """yt-dlp ን በመጠቀም ከቻናሉ የቪዲዮ/ኦዲዮ ፖስቶችን በቀጥታ መፈለግ"""
    channel_url = f"https://t.me/s/{CHANNEL_USERNAME}"
    print(f"[+] በ yt-dlp ከ {channel_url} መረጃዎችን በማውጣት ላይ...")
    
    ydl_opts = {
        'extract_flat': 'in_playlist',
        'quiet': True,
        'skip_download': True,
        'playlistend': 15,  # የመጨረሻዎቹን 15 ፖስቶች መውሰድ
    }
    
    post_urls = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
            if info and 'entries' in info:
                for entry in info['entries']:
                    url = entry.get('url') or entry.get('webpage_url')
                    if url:
                        post_urls.append(url)
    except Exception as e:
        print(f"⚠️ yt-dlp extraction error: {e}")
        
    return post_urls

def get_fallback_posts():
    """yt-dlp ካልሰራ በቀጥታ የቴሌግራም ገጽን በመጠየቅ"""
    url = f"https://t.me/s/{CHANNEL_USERNAME}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    import re
    try:
        r = requests.get(url, headers=headers, timeout=10)
        found = re.findall(r'data-post="' + CHANNEL_USERNAME + r'/(\d+)"', r.text)
        if found:
            post_ids = [int(x) for x in found]
            max_id = max(post_ids)
            return [f"https://t.me/{CHANNEL_USERNAME}/{i}" for i in range(max_id, max(1, max_id - 10), -1)]
    except Exception as e:
        print(f"Fallback error: {e}")
            
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
    
    post_urls = get_channel_posts_via_ytdlp()
    
    if not post_urls:
        print("⚠️ yt-dlp ፖስት ማግኘት አልቻለም፤ ሁለተኛ አማራጭ (Fallback) በመሞከር ላይ...")
        post_urls = get_fallback_posts()
        
    if not post_urls:
        print("⚠️ ምንም አይነት ፖስት ማግኘት አልተቻለም።")
        return

    print(f"✅ በጠቅላላ {len(post_urls)} የሚፈተሹ ፖስቶች ተገኝተዋል!")
    print(f"ፖስቶች፦ {post_urls}")

    print("\nWhisper AI (Small model) በመጫን ላይ...")
    model = whisper.load_model("small")
    
    found_audio_count = 0
    
    for idx, post_url in enumerate(post_urls, start=1):
        audio_filename = f"downloads/audio_{idx}.mp3"
        
        print(f"\n--------------------------------------------------")
        print(f"[+] ፖስት {idx} በመፈተሽ ላይ፦ {post_url}")
        
        try:
            download_audio(post_url, audio_filename)
            
            if os.path.exists(audio_filename):
                found_audio_count += 1
                print("✅ የድምፅ ፋይል ተገኝቷል! ወደ አማርኛ ጽሁፍ እየተቀየረ ነው...")
                result = model.transcribe(audio_filename, language="am")
                extracted_text = result["text"]
                
                if extracted_text.strip():
                    print("ጽሁፉን በቴሌግራም ቦት በመላክ ላይ...")
                    send_telegram_message(f"📍 **የፖስት ሊንክ፦** {post_url}\n\n" + extracted_text)
                    print(f"✅ ፖስት {idx} በቦት ተልኳል!")
                else:
                    print("⚠️ በድምፁ ውስጥ ምንም ጽሁፍ አልተገኘም።")
                    
                os.remove(audio_filename)
            else:
                print("ℹ️ በዚህ ፖስት ላይ ኦዲዮ አልተገኘም።")
                
        except Exception:
            print(f"ℹ️ በዚህ ፖስት ላይ ኦዲዮ አልተገኘም ወይም የጽሁፍ ፖስት ነው (ይዘለላል)።")

    if found_audio_count == 0:
        print("\n⚠️ በተፈተሹት ፖስቶች ውስጥ ምንም ኦዲዮ አልተገኘም።")

if __name__ == "__main__":
    main()
