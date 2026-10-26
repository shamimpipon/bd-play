import json
import os
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error

# ============================================================
# কনফিগারেশন - Shamim IPTV (১০০% স্বাধীন সংস্করণ)
# ============================================================
PLAYLIST_NAME = "Shamim IPTV - Toffee Live"
OWNER_NAME = "Shamim IPTV"
TELEGRAM_URL = "https://t.me/shamim_iptv"

JSON_FILE = "toffee_playlist.json"
M3U_FILE = "toffee_playlist.m3u"

def get_token_directly_from_toffee():
    """
    সরাসরি Toffee-র অফিশিয়াল সার্ভার থেকে লাইভ edge-cache-token সংগ্রহ করার ফাংশন
    (অন্য কোনো তৃতীয় পক্ষ বা কারো রিপোজিটরির সাহায্য ছাড়াই)
    """
    print("[*] Connecting directly to Toffee official server...")
    try:
        # ধাপ ১: Toffee ওয়েবসাইট থেকে গেস্ট ডিভাইস কুকি সংগ্রহ
        home_url = "https://toffeelive.com"
        req = urllib.request.Request(home_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
        
        with urllib.request.urlopen(req, timeout=15) as res:
            headers = res.info()
            raw_cookies = headers.get_all('Set-Cookie') or []
        
        device_token = None
        cookie_parts = []
        for c in raw_cookies:
            first_part = c.split(';')[0]
            cookie_parts.append(first_part)
            if first_part.startswith("device_token="):
                device_token = first_part.replace("device_token=", "").strip()

        if not device_token:
            print("[-] Direct extraction: device_token not found in initial cookies.")
            return None

        # ধাপ ২: Toffee Playback API থেকে লাইভ স্ট্রিমিং টোকেন নেওয়া
        playback_url = "https://entitlement-prod.services.toffeelive.com/toffee/BD/DK/web/playback/Xi_Ga5oBNnOkwJLWkhKP"
        cookie_header = "; ".join(cookie_parts)
        
        post_req = urllib.request.Request(playback_url, data=b"{}", headers={
            "Origin": "https://toffeelive.com",
            "Referer": "https://toffeelive.com/",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {device_token}",
            "Cookie": cookie_header,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        with urllib.request.urlopen(post_req, timeout=15) as pb_res:
            pb_data = json.loads(pb_res.read().decode('utf-8'))
            stream_url = pb_data.get("playbackDetails", {}).get("data", [{}])[0].get("url", "")
            
            if "edge-cache-token=" in stream_url:
                token = stream_url.split("edge-cache-token=")[1]
                print(f"[✓] SUCCESS! Token generated directly from Toffee official server!")
                return token

    except Exception as e:
        print(f"[-] Direct extraction error: {e}")
    
    return None

def update_playlist():
    if not os.path.exists(JSON_FILE):
        print(f"[!] Error: {JSON_FILE} not found.")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # সরাসরি Toffee সার্ভার থেকে টোকেন সংগ্রহ
    token = get_token_directly_from_toffee()

    if not token:
        print("[!] Warning: Could not generate new token directly. Keeping existing token.")
    else:
        print(f"[+] Applying fresh token to all 75 channels...")

    # বাংলাদেশ সময় (UTC + 6 ঘণ্টা)
    bd_time = datetime.now(timezone(timedelta(hours=6)))
    now_str = bd_time.strftime("%I:%M:%S %p %d-%m-%Y")

    data["playlist_info"] = {
        "name": PLAYLIST_NAME,
        "telegram": TELEGRAM_URL,
        "owner": OWNER_NAME,
        "last_update": now_str
    }

    m3u_lines = [
        "#EXTM3U",
        f"# name: {PLAYLIST_NAME}",
        f"# telegram: {TELEGRAM_URL}",
        f"# owner: {OWNER_NAME}",
        f"# last_update: {now_str}",
        ""
    ]

    active_count = 0
    for ch in data.get("channels", []):
        old_url = ch.get("stream_url", "")
        if not old_url or old_url == "N/A":
            continue

        base_url = old_url.split("?")[0]
        if token:
            updated_stream_url = f"{base_url}?edge-cache-token={token}"
            ch["stream_url"] = updated_stream_url
        else:
            updated_stream_url = old_url

        ch_id = ch.get("channel_id", "")
        ch_name = ch.get("channel_name", "")
        logo = ch.get("logo_url", "")
        category = ch.get("category", "General")

        m3u_lines.append(f'#EXTINF:-1 tvg-id="{ch_id}" tvg-name="{ch_name}" tvg-logo="{logo}" group-title="{category}",{ch_name}')
        m3u_lines.append(updated_stream_url)
        m3u_lines.append("")
        active_count += 1

    # JSON ফাইল সেভ
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"[✓] {JSON_FILE} updated successfully.")

    # M3U ফাইল সেভ
    with open(M3U_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    print(f"[✓] {M3U_FILE} generated successfully with {active_count} active channels.")

if __name__ == "__main__":
    update_playlist()
