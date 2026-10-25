import json
import os
from datetime import datetime
import urllib.request
import urllib.error

# ============================================================
# কনফিগারেশন - Shamim IPTV
# ============================================================
PLAYLIST_NAME = "Shamim IPTV - Toffee Live"
OWNER_NAME = "Shamim IPTV"
TELEGRAM_URL = "https://t.me/shamim_iptv"

JSON_FILE = "toffee_playlist.json"
M3U_FILE = "toffee_playlist.m3u"

# বিকল্প ব্যাকআপ মিরর (যদি Toffee সার্ভার সরাসরি কোনো কারণে রেসপন্স না করে)
FALLBACK_MIRRORS = [
    "https://raw.githubusercontent.com/srhady/toffee-bd/main/toffee_playlist.json",
    "https://raw.githubusercontent.com/Jeshan-akand/Toffee-Channels-Link-Headers/main/toffee_channel_data.json"
]

def get_token_directly_from_toffee():
    """
    Toffee-র অফিশিয়াল সার্ভার থেকে সরাসরি ফ্রেশ edge-cache-token সংগ্রহ করার ফাংশন
    """
    print("[*] Attempting direct token extraction from Toffee servers...")
    try:
        # ধাপ ১: Toffee হোমপেজে ভিজিট করে device_token এবং কুকি সংগ্রহ
        home_url = "https://toffeelive.com"
        req = urllib.request.Request(home_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
        
        with urllib.request.urlopen(req, timeout=12) as res:
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

        # ধাপ ২: Toffee Playback API কল করা (Somoy TV চ্যানেল আইডি ব্যবহার করে)
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
        
        with urllib.request.urlopen(post_req, timeout=12) as pb_res:
            pb_data = json.loads(pb_res.read().decode('utf-8'))
            
            # স্ট্রিম ইউআরএল থেকে edge-cache-token আলাদা করা
            stream_url = pb_data.get("playbackDetails", {}).get("data", [{}])[0].get("url", "")
            if "edge-cache-token=" in stream_url:
                token = stream_url.split("edge-cache-token=")[1]
                print(f"[✓] SUCCESS! Token directly generated from Toffee server: {token[:35]}...")
                return token

    except Exception as e:
        print(f"[-] Direct Toffee extraction error: {e}")
    
    return None

def fetch_token_from_mirrors():
    """
    বিকল্প মিরর থেকে টোকেন সংগ্রহকারী ফাংশন (ফলব্যাক)
    """
    print("[*] Trying fallback mirrors...")
    for url in FALLBACK_MIRRORS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))
                channels = data.get("channels", [])
                for ch in channels:
                    url_val = ch.get("stream_url") or ch.get("link") or ""
                    if "edge-cache-token=" in url_val:
                        token = url_val.split("edge-cache-token=")[1]
                        if len(token) > 20:
                            print(f"[✓] Retrieved token from fallback mirror: {url}")
                            return token
        except Exception as e:
            print(f"[-] Mirror failed: {url}")
    return None

def update_playlist():
    if not os.path.exists(JSON_FILE):
        print(f"[!] Error: {JSON_FILE} not found.")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ১. প্রথমে সরাসরি Toffee সার্ভার থেকে টোকেন নেওয়ার চেষ্টা
    token = get_token_directly_from_toffee()
    
    # ২. যদি কোনো কারণে ফেইল করে, তাহলে বিকল্প মিরর ব্যবহার করা
    if not token:
        token = fetch_token_from_mirrors()

    if not token:
        print("[!] Warning: All token sources failed. Keeping current tokens.")
    else:
        print(f"[+] Applying token to all active channels...")

    now_str = datetime.now().strftime("%I:%M:%S %p %d-%m-%Y")

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

        m3u_lines.append(f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo}" group-title="{category}",{ch_name}')
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
