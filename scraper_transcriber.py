import os
import re
import requests
from bs4 import BeautifulSoup
import yt_dlp
import whisper

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHANNEL_USERNAME = "abagebrekidan"
CHANNEL_URL = f"https://t.me/s/{CHANNEL_USERNAME}"

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
        try:
            requests.post(url, data=payload)
        except Exception as e:
            print(f"መልእክት በመላክ ላይ ስህተት ተከሰተ፦ {e}")

def get_audio_post_urls():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    print(f"ገጹን ከ {CHANNEL_URL} በመጫን ላይ...")
    response = requests.get(CHANNEL_URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    post_urls = []
    messages = soup.find_all('div', class_='tgme_widget_message')
    print(f"በገጹ ላይ በጠቅላላ {len(messages)} ፖስቶች ተገኝተዋል።")
    
    for msg in messages:
        # የፖስቱን ሊንክ ማውጣት
        data_post = msg.get('data-post')
        date_anchor = msg.find('a', class_='tgme_widget_message_date')
        
        post_link = None
        if data_post:
            post_link = f"https://t.me/{data_post}"
        elif date_anchor and date_anchor.get('href'):
            post_link = date_anchor.get('href')
            
        if not post_link:
            continue
            
        # በፖስቱ ውስጥ ኦዲዮ/ድምፅ መኖሩን በልዩ ልዩ መንገዶች መፈተሽ
        has_audio_tag = msg.find('audio') is not None
        has_voice = bool(msg.select('.tgme_widget_message_voice, .tgme_widget_message_voice_player, [class*="voice"]'))
        has_doc = bool(msg.select('.tgme_widget_message_document, .tgme_widget_message_document_wrap, [class*="document"]'))
        has_audio_ext = bool(re.search(r'\.(mp3|ogg|m4a|wav|aac|flac)\b', msg.text, re.IGNORECASE))
        
        if has_audio_tag or has_voice or has_doc or has_audio_ext:
            print(f"  [+] የድምፅ ፖስት ተለይቷል፦ {post_link}")
            post_urls.append(post_link)
            
    # የትኛውም የድምፅ ምልክት ባይገኝ እንኳ የመጨረሻዎቹን 5 ፖስቶች ቀጥታ ለመፈተሽ
    if not post_urls and messages:
        print("⚠️ የተለየ የድምፅ ምልክት ስላልተገኘ የመጨረሻዎቹን 5 ፖስቶች አውቶማቲክ እንፈትሻለን...")
        for msg in messages[-5:]:
            data_post = msg.get('data-post')
            if data_post:
                post_urls.append(f"https://t.me/{data_post}")
                
    # ድግግሞሾችን ማስወገድ
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
    
    post_urls = get_audio_post_urls()
    print(f"\n[+] ለምርመራ የተዘጋጁ ፖስቶች ብዛት፦ {len(post_urls)}")
    
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
            print(f"ℹ️ በዚህ ፖስት ላይ ኦዲዮ አልተገኘም ወይም ስህተት ተከሰተ (ይዘለላል)።")

if __name__ == "__main__":
    main()
