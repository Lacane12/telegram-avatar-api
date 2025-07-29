from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import json
import os
import time

app = Flask(__name__)

CACHE_FILE = "avatar_cache.json"
CACHE_TTL = 60 * 60  # 1 час
avatar_cache = {}  # username -> {'url': ..., 'timestamp': ...}


def load_cache():
    global avatar_cache
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            try:
                avatar_cache = json.load(f)
            except Exception:
                avatar_cache = {}


def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(avatar_cache, f, ensure_ascii=False, indent=2)


@app.route("/avatar")
def get_avatar():
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "Missing username"}), 400

    now = time.time()
    cached = avatar_cache.get(username)

    if cached and now - cached["timestamp"] < CACHE_TTL:
        return jsonify({"avatar": cached["url"]})

    try:
        url = f"https://t.me/{username}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        img_tag = soup.find("img", class_="tgme_page_photo_image")
        if not img_tag or not img_tag.get("src"):
            return jsonify({"error": "Avatar not found"}), 404

        avatar_url = img_tag["src"]

        avatar_cache[username] = {"url": avatar_url, "timestamp": now}
        save_cache()

        return jsonify({"avatar": avatar_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    load_cache()
    app.run(host="0.0.0.0", port=8080)
