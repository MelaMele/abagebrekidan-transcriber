import os
import re
import subprocess
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

def get_latest_post_ids():
    found_ids = set()
    
    # መንገድ 1፦ Linux curl ን መጠቀም (የቴሌግራምን እግድ ለማለፍ)
    print(f"[+] 'curl' በመጠቀም ከ https://t.me/s/{CHANNEL_USERNAME} የፖስት ቁጥሮችን በመፈለግ ላይ...")
    try:
        cmd = [
            'curl', '-sL',
            '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            '-H', 'Accept-Language: en-US,en;q=0.9',
            f'https://t.me/s/{CHANNEL_USERNAME}'
        ]
        html = subprocess.check_output(cmd, timeout=20).decode('utf-8', errors='ignore')
        matches = re.findall(rf'{CHANNEL_USERNAME}/(\d+)', html)
        for m in matches:
            found_ids.add(int(m))
        if found_ids:
            print(f"  ✅ ከቴሌግራም ገፅ {len(found_ids)} የፖስት ቁጥሮች ተገኝተዋል!")
    except Exception as e:
        print(f"  ⚠️ Curl Error: {e}")

    # መንገድ 2፦ DuckDuckGo Search (ተጨማሪ አማራጭ)
    if not found_ids:
        print("[+] በ DuckDuckGo በመፈለግ ላይ...")
        try:
            cmd_ddg = [
                'curl', '-sL',
                '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
                f'https://html.duckduckgo.com/html/?q=site:t.me/{CHANNEL_USERNAME}/'
            ]
            html_ddg = subprocess.check_output(cmd_ddg, timeout=20).decode('utf-8', errors='ignore')
            matches_ddg = re.findall(rf'{CHANNEL_USERNAME}/(\d+)', html_ddg)
            for m in matches_ddg:
                found_ids.add(int(m))
            if found_ids:
                print(f"  ✅ ከ DuckDuckGo {len(found_ids)} የፖስት ቁጥሮች ተገኝተዋል!")
        except Exception as e:
            print(f"  ⚠️ DDG Error: {e}")

    if not found_ids:
        print("⚠️ ምንም የፖስት ቁጥር ማግኘት አልተቻለም።")
        return []

    max_id = max(found_ids)
    print(f"✅ የቅርብ ጊዜ የፖስት ቁጥር (Max Post ID)፦ {max_id}")
    
    # የመጨረሻዎቹን 15 ፖስቶች መውሰድ
    check_ids = list(range(max_id, max(1, max_id - 15), -1))
    return [f"https://t.me/{CHANNEL_USERNAME}/{pid}" for pid in check_ids]

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
    
    post_urls = get_latest_post_ids()
    
    if not post_urls:
        print("⚠️ የሚፈተሹ ፖስቶች አልተገኙም።")
        return

    print(f"\n[+] በጠቅላላ {len(post_urls)} ፖስቶች ይፈተሻሉ።")

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
