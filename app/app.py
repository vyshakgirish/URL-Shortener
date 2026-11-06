import os
import secrets
import string
from urllib.parse import urlparse

import redis
from flask import Flask, abort, jsonify, redirect, request

app = Flask(__name__)
r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)

ALPHABET = string.ascii_letters + string.digits
BASE_URL = os.getenv("BASE_URL", "http://localhost").rstrip("/")


def make_code(length=6):
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


@app.get("/healthz")
def healthz():
    r.ping()
    return {"status": "ok"}


@app.post("/api/shorten")
def shorten():
    url = (request.get_json(silent=True) or {}).get("url", "")
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return jsonify(error="Provide a valid http(s) URL"), 400

    for _ in range(5):  # retry on the (rare) code collision
        code = make_code()
        if r.set(f"link:{code}", url, nx=True):
            return jsonify(code=code, short_url=f"{BASE_URL}/{code}", url=url), 201
    return jsonify(error="Could not allocate a code"), 500


@app.get("/api/stats/<code>")
def stats(code):
    url = r.get(f"link:{code}")
    if not url:
        abort(404)
    return jsonify(code=code, url=url, hits=int(r.get(f"hits:{code}") or 0))


@app.get("/<code>")
def follow(code):
    url = r.get(f"link:{code}")
    if not url:
        abort(404)
    r.incr(f"hits:{code}")
    return redirect(url, code=302)
