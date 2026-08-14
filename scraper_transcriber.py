import os
import requests
from bs4 import BeautifulSoup
import yt_dlp
import whisper

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

def get_audio_post_urls():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    response = requests.get(CHANNEL_URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    post_urls = []
    # በቴሌግራም ገጽ ውስጥ ያሉትን መልእክቶች መፈተሽ
    messages = soup.find_all('div', class_='tgme_widget_message')
    
    for msg in messages:
        # በፖስቱ ውስጥ ኦዲዮ፣ ድምፅ ወይም ሰነድ ካለ መፈተሽ
        audio_tag = msg.find('audio')
        doc_tag = msg.find('a', class_='tgme_widget_message_document_wrap')
        voice_tag = msg.find('a', class_='tgme_widget_message_voice_player')
        
        if audio_tag or doc_tag or voice_tag:
            post_id = msg.get('data-post')
            if post_id:
                post_urls.append(f"https://t.me/{post_id}")
                
    return list(set(post_urls))

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
    print("የቻናሉን ገፅ በመፈተሽ ላይ...")
    
    post_urls = get_audio_post_urls()
    print(f"\n[+] በጠቅላላ {len(post_urls)} የድምፅ ፖስቶች ተገኝተዋል።")
    
    if not post_urls:
        print("⚠️ ምንም የድምፅ ፖስት አልተገኘም።")
        return

    print("\nWhisper AI (Small model) በመጫን ላይ...")
    model = whisper.load_model("small")
    
    for idx, post_url in enumerate(post_urls, start=1):
        audio_filename = f"downloads/audio_{idx}.mp3"
        print(f"\n[+] ፖስት {idx} በማውረድ ላይ: {post_url}")
        
        try:
            download_audio(post_url, audio_filename)
            
            # ፋይሉ ከወረደ ወደ ጽሁፍ መቀየር
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
            print(f"❌ ስህተት ተከሰተ፦ {e}")

if __name__ == "__main__":
    main()
