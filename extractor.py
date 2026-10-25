import json
import os
import re
from datetime import datetime
import urllib.request

# ============================================================
# কনফিগারেশন - আপনার ব্র্যান্ডের তথ্য
# ============================================================
PLAYLIST_NAME = "Shamim IPTV - Toffee Live"
OWNER_NAME = "Shamim"
TELEGRAM_URL = "https://t.me/shamim_iptv"

JSON_FILE = "toffee_playlist.json"
M3U_FILE = "toffee_playlist.m3u"

# টোকেন সংগ্রহের সক্রিয় অনলাইন সোর্সসমূহ
TOKEN_MIRRORS = [
    "https://raw.githubusercontent.com/srhady/toffee-bd/main/toffee_playlist.json",
    "https://raw.githubusercontent.com/Jeshan-akand/Toffee-Channels-Link-Headers/main/toffee_channel_data.json"
]

def fetch_latest_token():
    for url in TOKEN_MIRRORS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                channels = data.get("channels", [])
                for ch in channels:
                    url_val = ch.get("stream_url") or ch.get("link") or ""
                    if "edge-cache-token=" in url_val:
                        token = url_val.split("edge-cache-token=")[1]
                        if len(token) > 20:
                            print(f"[✓] Successfully retrieved fresh token from: {url}")
                            return token
        except Exception as e:
            print(f"[-] Mirror failed: {url} -> {e}")
    return None

def update_playlist():
    if not os.path.exists(JSON_FILE):
        print(f"[!] Error: {JSON_FILE} not found.")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # নতুন ফ্রেশ টোকেন সংগ্রহ
    new_token = fetch_latest_token()
    if not new_token:
        print("[!] Could not fetch new token, keeping existing.")
    else:
        print(f"[✓] Applying active token: {new_token[:35]}...")

    now_str = datetime.now().strftime("%I:%M:%S %p %d-%m-%Y")

    data["playlist_info"] = {
        "name": PLAYLIST_NAME,
        "telegram": TELEGRAM_URL,
        "owner": OWNER_NAME,
        "last_update": now_str
    }

    # সব চ্যানেলের স্ট্রিমে নতুন টোকেন আপডেট করা
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
        if new_token:
            updated_stream_url = f"{base_url}?edge-cache-token={new_token}"
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
    print(f"[✓] {JSON_FILE} updated with {len(data.get('channels', []))} channels.")

    # M3U ফাইল সেভ
    with open(M3U_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))
    print(f"[✓] {M3U_FILE} generated with {active_count} active channels.")

if __name__ == "__main__":
    update_playlist()
