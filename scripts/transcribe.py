"""Transcribe a short Hindi clip with Gemini (used for captions on videos made outside the engine).
Usage: python3 scripts/transcribe.py transcribe/<name>.mp3  -> writes transcribe/<name>.json
Keys come only from GEMINI_API_KEY / GEMINI_API_KEY_2 env vars; never printed."""
import base64, json, os, sys, urllib.request

BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
MODELS = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"]
PROMPT = ("This is the audio of a short Hindi comedy video with two characters: a boy (Golu) and a middle-aged "
 "man (Masterji). Transcribe every spoken line exactly as said, in Devanagari Hindi (keep English words as spoken, "
 "in Devanagari). Give precise start and end times in seconds from the start of the audio. Split long lines at "
 "natural pauses so no item is longer than about 3 seconds. Ignore sound effects and breathing. Return JSON only: "
 '{"lines":[{"start":0.0,"end":0.0,"speaker":"Golu"|"Masterji","text":"..."}]}')

def call(model, key, audio):
    body = {"contents": [{"parts": [{"inline_data": {"mime_type": "audio/mp3", "data": audio}}, {"text": PROMPT}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0}}
    req = urllib.request.Request(BASE + model + ":generateContent", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "x-goog-api-key": key})
    with urllib.request.urlopen(req, timeout=180) as r:
        out = json.load(r)
    return json.loads(out["candidates"][0]["content"]["parts"][0]["text"])

src = sys.argv[1]
audio = base64.b64encode(open(src, "rb").read()).decode()
keys = [k for k in (os.environ.get("GEMINI_API_KEY", ""), os.environ.get("GEMINI_API_KEY_2", "")) if k.strip()]
last = ""
for key in keys:
    for m in MODELS:
        try:
            res = call(m, key.strip(), audio)
            res["model"] = m
            json.dump(res, open(src[:-4] + ".json", "w"), ensure_ascii=False, indent=1)
            print("OK", m, len(res.get("lines", [])), "lines")
            sys.exit(0)
        except Exception as e:
            last = str(e)
            for k in keys: last = last.replace(k, "***")
            print("try", m, "failed:", last[:160])
sys.exit("all models failed")
