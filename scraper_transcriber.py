import os
import re
import requests
from bs4 import BeautifulSoup
import whisper

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHANNEL_URL = "https://t.me/s/abagebrekidan"

def send_telegram_message(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Bot Token ወይም Chat ID አልተገኘም!")
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    # ቴሌግራም በአንድ መልእክት ከ4096 ፊደል በላይ ስለማይቀበል ረጅም ጽሁፍ ከሆነ ከፋፍሎ ለመላክ
    for i in range(0, len(text), 4000):
        chunk = text[i:i+4000]
        payload = {
            "chat_id": CHAT_ID,
            "text": f"📖 **የአባ ገብረኪዳን ትምህርት (በጽሁፍ)፦**\n\n{chunk}",
            "parse_mode": "Markdown"
        }
        requests.post(url, data=payload)

def get_audio_links():
    print("የቻናሉን ገፅ በመፈተሽ ላይ...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    }
    response = requests.get(CHANNEL_URL, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    audio_links = []
    
    # 1. ሁሉንም የኦዲዮ ታጎች መፈለግ
    for audio in soup.find_all('audio'):
        src = audio.get('src')
        if src:
            audio_links.append(src)
            
    # 2. የቴሌግራም Voice Message ማጫወቻ ሊንኮችን መፈለግ
    for a in soup.find_all('a', class_=['tgme_widget_message_voice_player', 'tgme_widget_message_document_wrap']):
        href = a.get('href')
        if href and ('http' in href):
            audio_links.append(href)
            
    # 3. በRegex ሊንኮችን በገጹ ምንጭ (Source code) ውስጥ አጣርቶ መፈለግ
    found_urls = re.findall(r'src="(https://[^"]+)"', response.text)
    for url in found_urls:
        if '.ogg' in url or '.mp3' in url or '.m4a' in url or 'voice' in url:
            audio_links.append(url)
            
    return list(set(audio_links))

def main():
    os.makedirs("downloads", exist_ok=True)
    
    audio_links = get_audio_links()
    print(f"በገጹ ላይ {len(audio_links)} የድምፅ ፋይሎች ተገኝተዋል።")
    
    if not audio_links:
        print("ምንም አዲስ የድምፅ ፋይል አልተገኘም።")
        return

    print("Whisper AI (Small model) በመጫን ላይ...")
    model = whisper.load_model("small")
    
    for idx, link in enumerate(audio_links, start=1):
        audio_filename = f"downloads/audio_{idx}.mp3"
        
        print(f"\n[+] ኦዲዮ {idx} በማውረድ ላይ: {link}")
        res = requests.get(link, stream=True)
        with open(audio_filename, 'wb') as f:
            for chunk in res.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    
        print(f"ኦዲዮ {idx} ወደ አማርኛ ጽሁፍ እየተቀየረ ነው...")
        result = model.transcribe(audio_filename, language="am")
        extracted_text = result["text"]
        
        # የተቀየረውን ጽሁፍ በቴሌግራም ቦት መላክ
        print(f"ጽሁፉን በቴሌግራም ቦት በመላክ ላይ...")
        send_telegram_message(extracted_text)
        
        print(f"✅ ኦዲዮ {idx} በቦት ተልኳል!")
        
        if os.path.exists(audio_filename):
            os.remove(audio_filename)

if __name__ == "__main__":
    main()
