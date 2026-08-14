import os
import re
import requests
import feedparser
from bs4 import BeautifulSoup
import yt_dlp
import whisper

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHANNEL_USERNAME = "abagebrekidan"

# የቴሌግራም RSS Feed ሊንኮች
RSS_FEEDS = [
    f"https://rsshub.app/telegram/channel/{CHANNEL_USERNAME}",
    f"https://tg.i-as.dev/rss/{CHANNEL_USERNAME}"
]

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

def get_post_urls_from_rss():
    post_urls = []
    
    for feed_url in RSS_FEEDS:
        print(f"ከ RSS Feed መረጃዎችን በመጫን ላይ፦ {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            if feed.entries:
                print(f"  [+] {len(feed.entries)} ፖስቶች ተገኝተዋል!")
                for entry in feed.entries:
                    link = entry.get('link', '')
                    if link:
                        post_urls.append(link)
                break
        except Exception as e:
            print(f"  ⚠️ ከዚህ Feed ማግኘት አልተቻለም፦ {e}")
            
    # RSS ካልሰራ በነጻ API በመጠቀም መሞከር
    if not post_urls:
        print("በነጻ Telegram API መረጃዎችን በመፈለግ ላይ...")
        try:
            api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            res = requests.get(api_url).json()
            # fallback post URL
            post_urls = [f"https://t.me/s/{CHANNEL_USERNAME}"]
        except Exception as e:
            print(f"API Error: {e}")

    return list(dict.fromkeys(post_urls))

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
    
    post_urls = get_post_urls_from_rss()
    print(f"\n[+] በጠቅላላ የተገኙ ፖስቶች ብዛት፦ {len(post_urls)}")
    
    if not post_urls:
        print("⚠️ ምንም አይነት ፖስት ማግኘት አልተቻለም።")
        return

    print("\nWhisper AI (Small model) በመጫን ላይ...")
    model = whisper.load_model("small")
    
    for idx, post_url in enumerate(post_urls, start=1):
        audio_filename = f"downloads/audio_{idx}.mp3"
        print(f"\n--------------------------------------------------")
        print(f"[+] ፖስት {idx} በማውረድ ላይ፦ {post_url}")
        
        try:
            download_audio(post_url, audio_filename)
            
            if os.path.exists(audio_filename):
                print("ወደ አማርኛ ጽሁፍ እየተቀየረ ነው...")
                result = model.transcribe(audio_filename, language="am")
                extracted_text = result["text"]
                
                if extracted_text.strip():
                    print("ጽሁፉን በቴሌግራም ቦት በመላክ ላይ...")
                    send_telegram_message(extracted_text)
                    print(f"✅ ፖስት {idx} በቦት ተልኳል!")
                else:
                    print("⚠️ በድምፁ ውስጥ ምንም ጽሁፍ አልተገኘም።")
                    
                os.remove(audio_filename)
            else:
                print("⚠️ ፋይሉን ማውረድ አልተቻለም።")
                
        except Exception as e:
            print(f"ℹ️ በዚህ ፖስት ላይ ኦዲዮ አልተገኘም ወይም ሊወርድ አልቻለም (ይዘለላል)።")

if __name__ == "__main__":
    main()
