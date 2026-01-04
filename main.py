import os
import time
import json
import requests

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")  # např. UCxxxx
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

CHECK_EVERY_SECONDS = int(os.getenv("CHECK_EVERY_SECONDS", "60"))
STATE_FILE = "state.json"


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {"last_live_video_id": None}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_live_video_id": None}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def get_current_live_video():
    """
    Vrátí tuple (video_id, title) pokud je kanál live, jinak (None, None)
    Používá YouTube Search endpoint s eventType=live.
    """
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": YOUTUBE_CHANNEL_ID,
        "eventType": "live",
        "type": "video",
        "maxResults": 1,
        "key": YOUTUBE_API_KEY,
    }
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    items = data.get("items", [])
    if not items:
        return None, None

    item = items[0]
    video_id = item["id"]["videoId"]
    title = item["snippet"]["title"]
    return video_id, title


def send_discord_everyone(message: str) -> None:
    payload = {
        "content": f"@everyone {message}",
        "allowed_mentions": {"parse": ["everyone"]},
    }
    r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=15)
    r.raise_for_status()


def main():
    if not (YOUTUBE_API_KEY and YOUTUBE_CHANNEL_ID and DISCORD_WEBHOOK_URL):
        raise SystemExit(
            "Chybí ENV proměnné: YOUTUBE_API_KEY, YOUTUBE_CHANNEL_ID, DISCORD_WEBHOOK_URL"
        )

    state = load_state()
    last_live_video_id = state.get("last_live_video_id")

    print("Bot běží. Kontroluju live status...")

    while True:
        try:
            video_id, title = get_current_live_video()

            if video_id:
                # Je live
                if video_id != last_live_video_id:
                    stream_url = f"https://www.youtube.com/watch?v={video_id}"
                    msg = f"🔴 **Stream právě začal!**\n**{title}**\n{stream_url}"
                    send_discord_everyone(msg)
                    print("Odesláno na Discord:", title, stream_url)

                    last_live_video_id = video_id
                    state["last_live_video_id"] = last_live_video_id
                    save_state(state)
                else:
                    print("Stále live (už oznámeno).")
            else:
                # Není live -> necháme last id, ať další nový stream pošle znovu
                print("Offline.")

        except Exception as e:
            print("Chyba:", repr(e))

        time.sleep(CHECK_EVERY_SECONDS)


if __name__ == "__main__":
    main()
