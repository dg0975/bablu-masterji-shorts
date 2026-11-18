"""
Google Gemini text-to-speech for skit characters (expressive acting: style per line, <laugh> tags).

Used by scripts/voice_job.py in GitHub Actions with the GEMINI_API_KEY repo secret (and by
make_short.py if GEMINI_API_KEY is set locally). Tries the newest TTS models first and falls back
to older ones, because model names and free-tier access change.
"""
import base64, io, json, time, urllib.error, urllib.request, wave

BASE = "https://generativelanguage.googleapis.com/v1beta/"
NEW_MODELS = ["gemini-3.8-flash-tts", "gemini-3.8-flash-lite-tts"]              # Interactions API
OLD_MODELS = ["gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts"]     # generateContent API
_good = {}   # model that worked in this process, reused for the next lines


def _post(url, body, key):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def _wav_from_pcm(pcm, rate=24000):
    b = io.BytesIO()
    with wave.open(b, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)
    return b.getvalue()


def _find_audio(obj):
    """dig the first base64 audio payload out of any response shape"""
    if isinstance(obj, dict):
        for k in ("data",):
            v = obj.get(k)
            if isinstance(v, str) and len(v) > 1000:
                return v, obj.get("mime_type") or obj.get("mimeType") or ""
        if "inlineData" in obj:
            d = obj["inlineData"]; return d.get("data"), d.get("mimeType", "")
        for v in obj.values():
            r = _find_audio(v)
            if r:
                return r
    elif isinstance(obj, list):
        for v in obj:
            r = _find_audio(v)
            if r:
                return r
    return None


def _new_api(model, text, voice, style, key):
    content = {"type": "text", "text": text}
    if style:
        content["annotations"] = [{"type": "speech_metadata", "style": style}]
    body = {"model": model, "input": [{"type": "user_input", "content": [content]}],
            "response_format": {"type": "audio"}, "generation_config": {"speech_config": [{"voice": voice}]}}
    return _post(BASE + "interactions", body, key)


def _old_api(model, text, voice, style, key):
    prompt = (f"Say this in Hindi, {style}: " if style else "Say this in Hindi: ") + text
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    return _post(BASE + f"models/{model}:generateContent", body, key)


def synth(text, voice, style, key, path):
    """write a WAV for one line; raises RuntimeError with the last API message on failure"""
    order = ([_good["m"]] if _good.get("m") else []) + [m for m in NEW_MODELS + OLD_MODELS if m != _good.get("m")]
    last = None
    for model in order:
        for attempt in range(3):
            try:
                resp = (_new_api if model in NEW_MODELS else _old_api)(model, text, voice, style, key)
                got = _find_audio(resp)
                if not got:
                    raise RuntimeError("no audio in response")
                data, mime = got
                raw = base64.b64decode(data)
                wav = raw if raw[:4] == b"RIFF" else _wav_from_pcm(raw)
                if len(wav) < 4000:
                    raise RuntimeError("empty audio")
                with open(path, "wb") as f:
                    f.write(wav)
                _good["m"] = model
                return model
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace")[:300].replace(key, "***")
                last = f"{model}: HTTP {e.code}: {msg}"
                if e.code == 429:                 # free-tier rate limit: wait and retry this model
                    time.sleep(25 + 15 * attempt); continue
                break                             # 400/403/404: try the next model
            except Exception as e:  # noqa
                last = f"{model}: {type(e).__name__}: {e}"
                time.sleep(3)
    raise RuntimeError(last or "gemini tts failed")
