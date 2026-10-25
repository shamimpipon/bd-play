import json
import os
from datetime import datetime

# ============================================================
# কনফিগারেশন - আপনার তথ্য অনুযায়ী পরিবর্তন করুন
# ============================================================
PLAYLIST_NAME = "Toffee BD Live TV"
OWNER_NAME = "My IPTV Network"
TELEGRAM_URL = "https://t.me/your_telegram_channel"

JSON_FILE = "toffee_playlist.json"
M3U_FILE = "toffee_playlist.m3u"

def update_playlist():
    if not os.path.exists(JSON_FILE):
        print(f"[!] Error: {JSON_FILE} not found.")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    now_str = datetime.now().strftime("%I:%M:%S %p %d-%m-%Y")
    
    # প্লেলিস্ট তথ্য আপডেট
    data["playlist_info"] = {
        "name": PLAYLIST_NAME,
        "telegram": TELEGRAM_URL,
        "owner": OWNER_NAME,
        "last_update": now_str
    }

    # JSON ফাইল সেভ
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"[✓] {JSON_FILE} updated successfully.")

    # M3U ফাইল তৈরি
    m3u_lines = [
        "#EXTM3U",
        f"# name: {PLAYLIST_NAME}",
        f"# telegram: {TELEGRAM_URL}",
        f"# owner: OWNER_NAME",
        f"# last_update: {now_str}",
        ""
    ]

    count = 0
    for ch in data.get("channels", []):
        stream_url = ch.get("stream_url", "")
        if not stream_url or stream_url == "N/A":
            continue

        ch_id = ch.get("channel_id", "")
        ch_name = ch.get("channel_name", "")
        logo = ch.get("logo_url", "")
        category = ch.get("category", "General")

        m3u_lines.append(f'#EXTINF:-1 tvg-id="{ch_id}" tvg-logo="{logo}" group-title="{category}",{ch_name}')
        m3u_lines.append(stream_url)
        m3u_lines.append("")
        count += 1

    with open(M3U_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(m3u_lines))

    print(f"[✓] {M3U_FILE} generated successfully with {count} active channels.")

if __name__ == "__main__":
    update_playlist()
