"""
Sarvam AI (Bulbul) Hindi voice for hindi-shorts-maker.

Used two ways:
  * by scripts/voice_job.py inside GitHub Actions, where SARVAM_API_KEY is a repo secret;
  * by make_short.py, which reads the finished clips (or calls the API itself if
    SARVAM_API_KEY happens to be set in its environment).
Clip file names come from clip_key(), so both sides agree on which clip belongs to which line.
"""
import base64, hashlib, json, time, urllib.error, urllib.request

API = "https://api.sarvam.ai/text-to-speech"
DEFAULTS = {"model": "bulbul:v4-flash", "speaker": "harpreet_pa_narration", "pace": 0.97}


def settings(sb):
    """voice settings from storyboard fields sarvam_model / sarvam_speaker / sarvam_pace"""
    return {k: sb.get("sarvam_" + k, v) for k, v in DEFAULTS.items()}


def beat_cfg(sb, i, j):
    """voice settings for one line: skits give each character its own Sarvam speaker via sb["cast"]"""
    cfg = settings(sb)
    b = sb["scenes"][i]["beats"][j]
    who = b.get("who")
    v = (sb.get("cast") or {}).get(who) or {}
    if v.get("voice"):
        cfg = dict(cfg, speaker=v["voice"])
    if v.get("pace"):
        cfg = dict(cfg, pace=v["pace"])
    if b.get("voice"):
        cfg = dict(cfg, speaker=b["voice"])
    if v.get("engine") == "gemini" or b.get("engine") == "gemini":     # expressive Google voice
        cfg = {"engine": "gemini", "voice": b.get("gvoice") or v.get("gvoice", "Puck"),
               "style": b.get("style") or v.get("style", "")}
    return cfg


def clip_key(cfg, text):
    if cfg.get("engine") == "gemini":
        return hashlib.md5(f"gemini|{cfg['voice']}|{cfg['style']}|{text}".encode()).hexdigest()[:16]
    return hashlib.md5(f"sarvam|{cfg['model']}|{cfg['speaker']}|{cfg['pace']}|{text}".encode()).hexdigest()[:16]


def lines(sb):
    """(scene, beat, text) for every beat that has narration"""
    for i, s in enumerate(sb["scenes"]):
        for j, b in enumerate(s["beats"]):
            t = (b.get("say") or "").strip()
            if t:
                yield i, j, t


def _post(body, api_key):
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method="POST",
                                 headers={"api-subscription-key": api_key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())


def synth(text, cfg, api_key, path):
    """write a WAV clip for one line; raises RuntimeError with Sarvam's message on failure"""
    body = {"text": text, "target_language_code": "hi-IN", "model": cfg["model"],
            "speaker": cfg["speaker"], "pace": cfg["pace"], "speech_sample_rate": 24000}
    last = None
    for attempt in range(4):
        try:
            data = _post(body, api_key)
            audio = b"".join(base64.b64decode(a) for a in data["audios"])
            if len(audio) < 2000:
                raise RuntimeError("empty audio")
            with open(path, "wb") as f:
                f.write(audio)
            return
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            last = f"HTTP {e.code}: {msg}"
            if e.code in (400, 422) and "language" in msg and "target_language_code" in body:
                body["language_code"] = body.pop("target_language_code")   # older/newer field name
                continue
            if e.code in (401, 403):
                break                                                    # bad key: retrying will not help
        except Exception as e:  # noqa
            last = f"{type(e).__name__}: {e}"
        time.sleep(2 + 3 * attempt)
    raise RuntimeError(last or "unknown error")
