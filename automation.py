import json
import time
import os
from instagrapi import Client
from dotenv import load_dotenv

load_dotenv()

INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
STATE_FILE = "state.json"

def load_reels_from_collections():
    with open("saved_collections.json", "r", encoding="utf-8") as f:
        collections = json.load(f)
    
    reels = []
    for collection in collections:
        for item in collection.get("label_values", []):
            if isinstance(item, dict) and "dict" in item:
                for media in item["dict"]:
                    if isinstance(media, dict) and "dict" in media:
                        for m in media["dict"]:
                            if isinstance(m, dict) and m.get("label") == "URL" and "/reel/" in m.get("value", ""):
                                reels.append({"reel_url": m["value"]})
    return reels

def get_today_index():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
        return state.get("current_index", 0)
    return 0

def save_today_index(index):
    with open(STATE_FILE, "w") as f:
        json.dump({"current_index": index, "updated": time.strftime("%Y-%m-%d")}, f)

def handle_progress_command(user_id, cl):
    """Handle /progress command from recipient"""
    try:
        with open("state.json", "r") as f:
            state = json.load(f)
        reels = load_reels_from_collections()
        current = state.get("current_index", 0)
        msg = f"📊 Reel Automation Progress\n\n✅ Sent: {current}\n📊 Total: {len(reels)}\n📥 Remaining: {len(reels) - current}"
        cl.direct_send(text=msg, user_ids=[user_id])
        print(f"Sent progress info to user {user_id}")
    except Exception as e:
        print(f"Error handling progress command: {e}")

def run_daily(recipient_username="omf1.x"):
    reels = load_reels_from_collections()
    if not reels:
        print("No reels found")
        return 0
    
    current_index = get_today_index()
    if current_index >= len(reels):
        current_index = 0
    
    reel = reels[current_index]
    sent_count = 0
    
    cl = Client()
    try:
        cl.load_settings("session.json")
        print("Loaded existing session")
    except Exception as e:
        print(f"Failed to load session, logging in fresh: {e}")
    
    try:
        cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, relogin=False)
        print(f"Logged in as: {INSTAGRAM_USERNAME}")
    except Exception as e:
        print(f"Session expired, re-login required: {e}")
        cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        print(f"Logged in as: {INSTAGRAM_USERNAME}")
    
    user_id = cl.user_id_from_username(recipient_username)
    print(f"Sending to user_id: {user_id} ({recipient_username})")
    
    try:
        progress_msg = f"Reel {current_index + 1}/{len(reels)} - {reel['reel_url']}"
        cl.direct_send(text=progress_msg, user_ids=[user_id])
        sent_count = 1
        print(f"Sent reel {current_index + 1}/{len(reels)}: {reel['reel_url']}")
    except Exception as e:
        print(f"Error sending {reel['reel_url']}: {e}")
    
    save_today_index(current_index + 1)
    cl.dump_settings("session.json")
    return sent_count

if __name__ == "__main__":
    run_daily(recipient_username="omprakaash.bicarbonate__")