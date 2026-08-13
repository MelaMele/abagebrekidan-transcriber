import os
import re
import requests
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

def extract_audio_urls():
    print("የቻናሉን ገፅ በመፈተሽ ላይ...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(CHANNEL_URL, headers=headers)
    html_content = response.text
    
    # በቴሌግራም ገጽ ውስጥ ያሉትን ሁሉንም የድምፅ/ኦዲዮ ፋይል ሊንኮች በRegex መፈለግ
    # ቴሌግራም ድምፆችን በ'https://cdn...' ወይም 'https://t.me/i/...' ሊንኮች ነው የሚያስቀምጣቸው
    patterns = [
        r'https://[^"]+\.(?:ogg|mp3|m4a)\?[^"]+',
        r'https://t\.me/s/abagebrekidan/[0-9]+\?single',
        r'src="(https://[^"]+)"'
    ]
    
    audio_links = []
    for pattern in patterns:
        matches = re.findall(pattern, html_content)
        for match in matches:
            if '.ogg' in match or '.mp3' in match or '.m4a' in match or 'voice' in match:
                audio_links.append(match)
                
    # ከተደጋገሙ ማጽዳት
    unique_links = list(set(audio_links))
    return unique_links

def main():
    os.makedirs("downloads", exist_ok=True)
    
    audio_links = extract_audio_urls()
    print(f"\n[+] በጠቅላላ {len(audio_links)} የድምፅ ፋይሎች ተገኝተዋል።")
    
    if not audio_links:
        print("⚠️ ምንም የድምፅ ፋይል ማግኘት አልተቻለም።")
        return

    print("\nWhisper AI (Small model) በመጫን ላይ...")
    model = whisper.load_model("small")
    
    for idx, link in enumerate(audio_links, start=1):
        audio_filename = f"downloads/audio_{idx}.ogg"
        
        print(f"\n[+] ኦዲዮ {idx} በማውረድ ላይ: {link}")
        try:
            res = requests.get(link, stream=True)
            with open(audio_filename, 'wb') as f:
                for chunk in res.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
                        
            print(f"ኦዲዮ {idx} ወደ አማርኛ ጽሁፍ እየተቀየረ ነው...")
            result = model.transcribe(audio_filename, language="am")
            extracted_text = result["text"]
            
            if extracted_text.strip():
                print(f"ጽሁፉን በቴሌግራም ቦት በመላክ ላይ...")
                send_telegram_message(extracted_text)
                print(f"✅ ኦዲዮ {idx} በቦት ተልኳል!")
            else:
                print(f"⚠️ በኦዲዮ {idx} ውስጥ ምንም ድምፅ አልተገኘም።")
                
        except Exception as e:
            print(f"❌ ስህተት ተከሰተ፦ {e}")
            
        if os.path.exists(audio_filename):
            os.remove(audio_filename)

if __name__ == "__main__":
    main()
