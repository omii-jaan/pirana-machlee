import os
import json
from flask import Flask, jsonify, request
from instagrapi import Client
from automation import run_daily, load_reels_from_collections

app = Flask(__name__)

@app.route('/trigger', methods=['GET', 'POST'])
def trigger():
    recipient = request.args.get('recipient', 'target_username')
    try:
        sent = run_daily(recipient_username=recipient)
        return jsonify({"status": "success", "message": f"Automation completed, sent {sent} reels"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/send-progress', methods=['GET', 'POST'])
def send_progress():
    recipient = request.args.get('recipient', 'target_username')
    INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
    INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
    try:
        reels = load_reels_from_collections()
        with open("state.json", "r") as f:
            state = json.load(f)
        current = state.get("current_index", 0)
        msg = f"Reel Automation Progress\n\nSent: {current}\nTotal: {len(reels)}\nRemaining: {len(reels) - current}"
        cl = Client()
        cl.load_settings("session.json")
        cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD, relogin=False)
        user_id = cl.user_id_from_username(recipient)
        cl.direct_send(text=msg, user_ids=[user_id])
        return jsonify({"status": "success", "message": f"Progress sent to {recipient}"})
    except Exception as e:
        try:
            cl = Client()
            cl.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
            user_id = cl.user_id_from_username(recipient)
            cl.direct_send(text=msg, user_ids=[user_id])
            cl.dump_settings("session.json")
            return jsonify({"status": "success", "message": f"Progress sent to {recipient}"})
        except Exception as e2:
            return jsonify({"status": "error", "message": str(e2)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

@app.route('/progress', methods=['GET'])
def progress():
    try:
        with open("state.json", "r") as f:
            state = json.load(f)
        reels = load_reels_from_collections()
        return jsonify({
            "current_index": state.get("current_index", 0),
            "total_reels": len(reels),
            "updated": state.get("updated", "never"),
            "next_reel": reels[state.get("current_index", 0)] if reels else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "app": "Instagram Reel Automation",
        "endpoints": ["/trigger", "/health", "/progress", "/send-progress"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)