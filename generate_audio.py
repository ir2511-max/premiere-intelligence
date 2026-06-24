#!/usr/bin/env python3
"""
Generates the daily audio from latest_briefing.json.
Independent of Anthropic — only needs OPENAI_API_KEY + Resend is not used here.
This mirrors test_email.py exactly, which is known to work.
"""
import os, json, httpx

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
AUDIO_DIR = "audio"

print(f"Audio key length: {len(OPENAI_API_KEY)}")
if not OPENAI_API_KEY:
    print("ERROR: OPENAI_API_KEY missing — cannot generate audio")
    raise SystemExit(1)

with open("latest_briefing.json") as f:
    data = json.load(f)

date_slug = data["date_slug"]

# Build a clean English script
parts = [f"Good morning. Today is {data['date']}. Welcome to Premiere Intelligence, your daily luxury-tech briefing.",
         f"Today's signal: {data['lede']}"]
for i, s in enumerate(sorted(data["stories"], key=lambda x: -x["score"]), 1):
    parts.append(f"Story {i}. {s['headline']}. {s['summary']}")
parts.append("That's your Premiere Intelligence briefing. Have a sharp day.")
script = " ".join(parts)[:4096]

os.makedirs(AUDIO_DIR, exist_ok=True)
r = httpx.post(
    "https://api.openai.com/v1/audio/speech",
    headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
    json={"model": "tts-1", "input": script, "voice": "nova"},
    timeout=60,
)
print(f"OpenAI status: {r.status_code}")
r.raise_for_status()
path = f"{AUDIO_DIR}/{date_slug}.mp3"
with open(path, "wb") as f:
    f.write(r.content)
print(f"✓ Audio saved → {path}")
