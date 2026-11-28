"""
Paints skit backgrounds with a Google image model (GitHub Actions, GEMINI_API_KEY / GEMINI_API_KEY_2 secrets).
Reads art/requests.json: {"style": "...", "items": [{"name": "train_night", "prompt": "..."}]}.
Writes artout/<name>.png plus artout/status.json (model used or the API error per image; never any key).
Images already on the `art` branch are kept unless their prompt changed.
"""
import base64, hashlib, json, os, sys, time, urllib.error, urllib.request

BASE = "https://generativelanguage.googleapis.com/v1beta/"
KEYS = [k for k in (os.environ.get("GEMINI_API_KEY"), os.environ.get("GEMINI_API_KEY_2")) if k]
PREFER = ["gemini-3-pro-image", "gemini-3-flash-image", "gemini-2.5-flash-image", "imagen-4.0-generate", "imagen-4.0-fast", "imagen-3.0", "gemini-2.0-flash-preview-image"]


def call(method, url, key, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={"x-goog-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.loads(r.read())


def err(e):
    if isinstance(e, urllib.error.HTTPError):
        try:
            return f"HTTP {e.code}: " + json.loads(e.read()).get("error", {}).get("message", "")[:300]
        except Exception:
            return f"HTTP {e.code}"
    return str(e)[:300]


def models(key):
    out, tok = [], ""
    for _ in range(10):
        d = call("GET", BASE + "models?pageSize=200" + (f"&pageToken={tok}" if tok else ""), key)
        for m in d.get("models", []):
            n = m["name"].split("/")[-1]; meth = m.get("supportedGenerationMethods", [])
            if ("image" in n or n.startswith("imagen")) and ("generateContent" in meth or "predict" in meth):
                out.append((n, "predict" if "predict" in meth and "generateContent" not in meth else "gen"))
        tok = d.get("nextPageToken")
        if not tok:
            break
    rank = lambda n: next((i for i, p in enumerate(PREFER) if n.startswith(p)), 99)
    return sorted(out, key=lambda x: (rank(x[0]), x[0]))


def find_img(o):
    if isinstance(o, dict):
        for k in ("inlineData", "inline_data"):
            if k in o and str(o[k].get("mimeType", o[k].get("mime_type", ""))).startswith("image"):
                return o[k]["data"]
        if "bytesBase64Encoded" in o:
            return o["bytesBase64Encoded"]
        for v in o.values():
            r = find_img(v)
            if r:
                return r
    elif isinstance(o, list):
        for v in o:
            r = find_img(v)
            if r:
                return r


def paint(model, kind, prompt, key):
    if kind == "predict":
        d = call("POST", BASE + f"models/{model}:predict", key, {"instances": [{"prompt": prompt}], "parameters": {"sampleCount": 1, "aspectRatio": "9:16"}})
    else:
        body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseModalities": ["IMAGE", "TEXT"], "imageConfig": {"aspectRatio": "9:16"}}}
        try:
            d = call("POST", BASE + f"models/{model}:generateContent", key, body)
        except urllib.error.HTTPError as e:
            if e.code != 400:
                raise
            body["generationConfig"].pop("imageConfig")
            body["contents"][0]["parts"][0]["text"] = prompt + " Vertical portrait image, aspect ratio 9:16."
            d = call("POST", BASE + f"models/{model}:generateContent", key, body)
    b = find_img(d)
    if not b:
        raise RuntimeError("no image in response: " + json.dumps(d)[:200])
    return base64.b64decode(b)


def main():
    req = json.load(open("art/requests.json"))
    os.makedirs("artout", exist_ok=True)
    prev = {}
    if os.path.exists("artprev/status.json"):
        prev = json.load(open("artprev/status.json")).get("items", {})
    st = {"ok": True, "models": [], "items": {}, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if not KEYS:
        st.update(ok=False, error="no GEMINI_API_KEY secret"); json.dump(st, open("artout/status.json", "w"), indent=1); return
    cands, why = [], ""
    for k in KEYS:
        try:
            cands = models(k)
            break
        except Exception as e:
            why = err(e)
    st["models"] = [m for m, _ in cands]
    if not cands:
        st.update(ok=False, error="no image model listed for this key " + why)
    style = req.get("style", "")
    for it in req["items"]:
        name, prompt = it["name"], (style + " " + it["prompt"]).strip()
        h = hashlib.md5(prompt.encode()).hexdigest()
        if prev.get(name, {}).get("md5") == h and os.path.exists(f"artprev/{name}.png"):
            os.replace(f"artprev/{name}.png", f"artout/{name}.png"); st["items"][name] = prev[name]; continue
        res = {"md5": h, "ok": False, "tries": []}
        for model, kind in cands:
            done = False
            for k in KEYS:
                try:
                    png = paint(model, kind, prompt, k)
                    open(f"artout/{name}.png", "wb").write(png)
                    res.update(ok=True, model=model); done = True; break
                except Exception as e:
                    res["tries"].append(f"{model}: {err(e)}")
            if done:
                break
        st["items"][name] = res
        if not res["ok"]:
            st["ok"] = False
        print(name, "OK " + res.get("model", "") if res["ok"] else "FAILED " + (res["tries"][-1] if res["tries"] else "no models"), flush=True)
    json.dump(st, open("artout/status.json", "w"), indent=1)


if __name__ == "__main__":
    main()
