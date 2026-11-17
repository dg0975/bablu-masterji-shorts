#!/usr/bin/env python3
"""
make_short.py - turn a storyboard JSON into a vertical 1080x1920 short with Hindi voiceover.

  python3 make_short.py storyboard.json --out OUTDIR --check     # voice + timing + preview sheet (fast)
  python3 make_short.py storyboard.json --out OUTDIR             # full frame-by-frame render -> OUTDIR/short.mp4

Pipeline: text-to-speech per beat -> timeline from real audio lengths -> headless browser draws
every frame of assets/player.html -> ffmpeg joins frames + audio into an MP4.
"""
import argparse, asyncio, base64, hashlib, json, math, os, shutil, struct, subprocess, sys, time, wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"
SR = 44100
W, H = 1080, 1920
POSES = {"idle", "point", "think", "shock", "happy", "sad", "shrug", "wave"}
VTYPES = {"svg", "html", "cards", "bars", "list", "number", "compare"}


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw)


def pip_install(pkg):
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", pkg],
                   check=False, capture_output=True)


# ----------------------------------------------------------------------------- validation
def validate(sb):
    errs, warns = [], []
    scenes = sb.get("scenes") or []
    if not scenes:
        errs.append("storyboard has no scenes")
    if not 4 <= len(scenes) <= 9:
        warns.append(f"{len(scenes)} scenes; 5-7 works best for a 60 s short")
    for i, s in enumerate(scenes):
        tag = f"scene {i}"
        if not s.get("headline"):
            errs.append(f"{tag}: missing headline")
        beats = s.get("beats") or []
        if not beats:
            errs.append(f"{tag}: needs at least one beat")
        v = s.get("visual")
        if v and v.get("type") not in VTYPES:
            errs.append(f"{tag}: unknown visual type {v.get('type')!r} (use one of {sorted(VTYPES)})")
        for j, b in enumerate(beats):
            if b.get("pose") and b["pose"] not in POSES:
                errs.append(f"{tag} beat {j}: unknown pose {b['pose']!r} (use one of {sorted(POSES)})")
            if b.get("friendPose") and b["friendPose"] not in POSES:
                errs.append(f"{tag} beat {j}: unknown friendPose {b['friendPose']!r}")
            if not b.get("say") and not b.get("hold"):
                warns.append(f"{tag} beat {j}: no 'say' text; holding 1.2 s of silence")
            for k in ("bubble", "friend"):
                if b.get(k) and len(b[k]) > 34:
                    warns.append(f"{tag} beat {j}: {k} is {len(b[k])} chars; keep speech bubbles under ~30")
    return errs, warns


# ----------------------------------------------------------------------------- text to speech
def _trust_system_certs():
    """sandbox proxies re-sign TLS, so edge-tts must trust the system bundle; patch before importing it"""
    try:
        import certifi
        for ca in (os.environ.get("SSL_CERT_FILE"), "/etc/ssl/certs/ca-certificates.crt"):
            if ca and os.path.exists(ca):
                certifi.where = lambda ca=ca: ca
                return
    except ImportError:
        pass


def _edge_tts(text, voice, rate, path, pitch="+0Hz"):
    import edge_tts

    async def run():
        com = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        with open(path, "wb") as f:
            async for ch in com.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
    asyncio.run(asyncio.wait_for(run(), timeout=60))
    if os.path.getsize(path) < 800:
        raise RuntimeError("empty audio")


def _gtts(text, path):
    from gtts import gTTS
    gTTS(text, lang="hi").save(path)


def pick_engine(pref):
    order = ["edge", "gtts"] if pref == "auto" else [pref]
    _trust_system_certs()
    for eng in order:
        mod, pkg = ("edge_tts", "edge-tts") if eng == "edge" else ("gtts", "gTTS")
        try:
            __import__(mod)
        except ImportError:
            pip_install(pkg)
        try:
            __import__(mod)
            probe = "/tmp/_tts_probe.mp3"
            if eng == "edge":
                _edge_tts("नमस्ते", "hi-IN-MadhurNeural", "+0%", probe)
            else:
                _gtts("नमस्ते", probe)
            return eng
        except Exception as e:  # noqa
            print(f"  [tts] {eng} unavailable: {type(e).__name__}: {str(e)[:120]}")
    sys.exit("ERROR: no text-to-speech engine reachable (needs network access to Microsoft or Google TTS).")


def load_pcm(path, tempo=1.0):
    """decode any audio file to mono float samples at SR, trimming silence at both ends"""
    import numpy as np
    af = ["-af", f"atempo={tempo}"] if abs(tempo - 1) > .01 else []
    raw = sh(["ffmpeg", "-v", "error", "-i", str(path), *af, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"]).stdout
    a = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    loud = np.where(np.abs(a) > 0.012)[0]
    if len(loud):
        a = a[max(0, loud[0] - int(.03 * SR)): min(len(a), loud[-1] + int(.09 * SR))]
    return a


def synth_sarvam(sb, voice_dir):
    """Sarvam AI voice: clips made by the GitHub voice job (or directly if SARVAM_API_KEY is set)"""
    sys.path.insert(0, str(HERE))
    import sarvam_tts as st
    cfg = st.settings(sb)
    api_key = os.environ.get("SARVAM_API_KEY", "").strip()
    cdir = Path(voice_dir) / "clips"
    cdir.mkdir(parents=True, exist_ok=True)
    clips, missing = {}, []
    for i, j, text in st.lines(sb):
        f = cdir / f"{st.clip_key(cfg, text)}.wav"
        if not f.exists() and api_key:
            st.synth(text, cfg, api_key, str(f))
        if f.exists():
            clips[(i, j)] = load_pcm(f)
        else:
            missing.append(f"scene {i} beat {j}")
    if missing:
        sys.exit("ERROR: Sarvam clips missing for " + ", ".join(missing) +
                 ". Push the storyboard and run scripts/get_voice.sh first (or set SARVAM_API_KEY).")
    print(f"  [tts] engine: sarvam  speaker: {cfg['speaker']}  model: {cfg['model']}  pace: {cfg['pace']}")
    return clips, "sarvam"


def synth_all(sb, out, pref, voice_dir=None):
    if pref == "sarvam" or (pref == "auto" and sb.get("tts") == "sarvam"):
        return synth_sarvam(sb, voice_dir or (out / "voice"))
    cache = out / "tts"
    cache.mkdir(parents=True, exist_ok=True)
    voice, rate, pitch = sb.get("voice", "hi-IN-MadhurNeural"), sb.get("rate", "-2%"), sb.get("pitch", "-3Hz")
    eng = None
    clips = {}
    if pref == "silent":  # layout preview only: timing estimated from word count, no audio
        import numpy as np
        print("  [tts] SILENT PREVIEW: no voice, timing estimated (~0.37 s per word)")
        for i, s in enumerate(sb["scenes"]):
            for j, b in enumerate(s["beats"]):
                text = (b.get("say") or "").strip()
                if text:
                    clips[(i, j)] = np.zeros(int(len(text.split()) * 0.37 * SR), dtype=np.float32)
        return clips, "silent"
    for i, s in enumerate(sb["scenes"]):
        for j, b in enumerate(s["beats"]):
            text = (b.get("say") or "").strip()
            if not text:
                continue
            if eng is None:
                eng = pick_engine(pref)
                print(f"  [tts] engine: {eng}" + (f"  voice: {voice}  rate: {rate}  pitch: {pitch}" if eng == "edge" else "  (fallback Google voice, sped up)"))
            key = hashlib.md5(f"{eng}|{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:16]
            mp3 = cache / f"{key}.mp3"
            if not mp3.exists():
                for attempt in range(3):
                    try:
                        _edge_tts(text, voice, rate, str(mp3), pitch) if eng == "edge" else _gtts(text, str(mp3))
                        break
                    except Exception as e:  # noqa
                        if mp3.exists():
                            mp3.unlink()
                        if attempt == 2:
                            sys.exit(f"ERROR: TTS failed for scene {i} beat {j}: {e}")
                        time.sleep(1.5)
            clips[(i, j)] = load_pcm(mp3, 1.0 if eng == 'edge' else float(sb.get('gtts_tempo', 1.18)))
    return clips, eng


# ----------------------------------------------------------------------------- timeline + audio
def build_timeline(sb, clips):
    gap, lead = float(sb.get("gap", 0.28)), 0.5
    t, scenes = 0.0, []
    for i, s in enumerate(sb["scenes"]):
        st = t
        t += lead
        beats = []
        for j, b in enumerate(s["beats"]):
            d = len(clips[(i, j)]) / SR if (i, j) in clips else float(b.get("hold", 1.2))
            extra = float(b.get("pause", 0))
            beats.append({"start": round(t, 3), "audioEnd": round(t + d, 3), "end": round(t + d + gap + extra, 3)})
            t += d + gap + extra
        t += 0.15
        scenes.append({"start": round(st, 3), "end": round(t, 3), "beats": beats})
    total = t + float(sb.get("outro", 0.9))
    scenes[-1]["end"] = round(total, 3)
    return {"duration": round(total, 3), "scenes": scenes}


def music_bed(n):
    """soft royalty-free pad generated in code (no samples)"""
    import numpy as np
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float32)
    chords = [(220.0, 261.63, 329.63, 392.0), (174.61, 220.0, 261.63, 329.63), (196.0, 246.94, 293.66, 392.0), (164.81, 207.65, 246.94, 329.63)]
    seg = 4.0
    for k in range(int(math.ceil(n / SR / seg))):
        a, b = int(k * seg * SR), min(n, int((k + 1) * seg * SR))
        tt = t[a:b] - k * seg
        env = np.clip(tt / .9, 0, 1) * np.clip((seg - tt) / .9, 0, 1)
        for f in chords[k % len(chords)]:
            out[a:b] += (np.sin(2 * np.pi * f * tt) + .35 * np.sin(2 * np.pi * f * 2 * tt + 1)) * env * (.8 + .2 * np.sin(2 * np.pi * .4 * tt + f))
    out /= max(1e-6, np.abs(out).max())
    return out


ENV_FPS = 30


def voice_envelope(mix):
    """loudness of the voice track per video frame (0..1); drives Masterji's lip-sync and head nods"""
    import numpy as np
    hop = SR // ENV_FPS
    n = len(mix) // hop
    if n == 0:
        return None
    rms = np.sqrt((mix[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    ref = np.percentile(rms[rms > 1e-4], 92) if (rms > 1e-4).any() else 0
    if ref <= 0:
        return None
    env = np.clip(rms / ref, 0, 1) ** 0.7
    env[env < 0.12] = 0
    return [round(float(v), 2) for v in env]


def write_audio(sb, clips, tl, path):
    import numpy as np
    n = int(tl["duration"] * SR) + 1
    mix = np.zeros(n, dtype=np.float32)
    for (i, j), a in clips.items():
        s = int(tl["scenes"][i]["beats"][j]["start"] * SR)
        e = min(n, s + len(a))
        mix[s:e] += a[: e - s]
    pk = np.abs(mix).max()
    if pk > 0:
        mix *= 0.89 / pk
    env = voice_envelope(mix)
    if env:
        tl["env"], tl["envFps"] = env, ENV_FPS
    vol = sb.get("music", 0.05)
    if vol:
        bed = music_bed(n) * float(vol if vol is not True else 0.05)
        fade = int(.8 * SR)
        bed[:fade] *= np.linspace(0, 1, fade)
        bed[-fade:] *= np.linspace(1, 0, fade)
        mix += bed
    mix = np.clip(mix, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())


# ----------------------------------------------------------------------------- rendering
def write_page(sb, tl, out):
    html = (ASSETS / "player.html").read_text(encoding="utf-8")
    fdir = (ASSETS / "fonts").resolve()
    faces = "".join(
        f"@font-face{{font-family:'Poppins';font-weight:{wgt};src:url('file://{fdir}/Poppins-{name}.ttf')}}\n"
        for wgt, name in ((400, "Regular"), (500, "Medium"), (700, "Bold")) if (fdir / f"Poppins-{name}.ttf").exists())
    if (fdir / "Kalam-Bold.ttf").exists():
        faces += f"@font-face{{font-family:'Kalam';font-weight:700;src:url('file://{fdir}/Kalam-Bold.ttf')}}\n"
    data = "const SB=" + json.dumps(sb, ensure_ascii=False).replace("</", "<\\/") + ";\nconst TL=" + json.dumps(tl) + ";"
    html = html.replace("/*FONTS*/", faces).replace("/*DATA*/", data)
    page = out / "_page.html"
    page.write_text(html, encoding="utf-8")
    return page


def open_page(pw, page_path):
    try:
        browser = pw.chromium.launch(args=["--force-color-profile=srgb", "--font-render-hinting=none", "--disable-lcd-text"])
    except Exception:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
        browser = pw.chromium.launch(args=["--force-color-profile=srgb"])
    page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"file://{page_path.resolve()}")
    try:
        page.wait_for_function("window.__ready===true", timeout=20000)
    except Exception:
        sys.exit("ERROR: the page failed to start. " + (" | ".join(errors) or "Check custom svg/html in the storyboard for broken markup."))
    return browser, page, errors


def shot(cdp, page, t, quality=92):
    page.evaluate(f"renderAt({t:.4f})")
    r = cdp.send("Page.captureScreenshot", {"format": "jpeg", "quality": quality, "optimizeForSpeed": True})
    return base64.b64decode(r["data"])


def layout_report(page, tl):
    """measure overflow at the end of every scene so problems are caught before the long render"""
    js = """(t)=>{window.NOCAM=true; renderAt(t); window.NOCAM=false; const out=[]; const sc=[...document.querySelectorAll('.scene')].find(e=>e.style.display==='block');
      const v=sc.querySelector('.visual').getBoundingClientRect(), h=sc.querySelector('.head').getBoundingClientRect();
      if(h.bottom>592) out.push('header text runs into the visual by '+Math.round(h.bottom-592)+'px (shorten headline/sub)');
      for(const el of sc.querySelectorAll('.visual .c-fill > *')){const r=el.getBoundingClientRect();
        if(r.left<v.left-6||r.right>v.right+6||r.top<v.top-6||r.bottom>v.bottom+6){out.push('visual content overflows its 960x530 box (fewer/shorter items)');break}}
      for(const id of ['b0','b1']){const b=document.getElementById(id); if(+b.style.opacity>0){const r=b.getBoundingClientRect(); if(r.height>190) out.push('speech bubble too tall ('+b.textContent+')')}}
      return out}"""
    probs = []
    for i, s in enumerate(tl["scenes"]):
        for j, b in enumerate(s["beats"]):
            for p in page.evaluate(js, b["audioEnd"] - 0.02):
                msg = f"scene {i} beat {j}: {p}"
                if msg not in probs:
                    probs.append(msg)
    return probs


def preview_sheet(cdp, page, tl, out):
    from PIL import Image
    import io
    times = [b["audioEnd"] - 0.05 for s in tl["scenes"] for b in s["beats"]]
    if len(times) > 18:
        step = len(times) / 18
        times = [times[int(k * step)] for k in range(18)]
    tw, th = 300, 533
    cols = 6
    rows = math.ceil(len(times) / cols)
    sheet = Image.new("RGB", (cols * tw, rows * th), "#111")
    for k, t in enumerate(times):
        im = Image.open(io.BytesIO(shot(cdp, page, t, 85))).resize((tw, th), Image.LANCZOS)
        sheet.paste(im, ((k % cols) * tw, (k // cols) * th))
    p = out / "preview_sheet.jpg"
    sheet.save(p, quality=88)
    return p


def render_video(cdp, page, tl, audio, out, fps):
    n = int(math.ceil(tl["duration"] * fps))
    mp4 = out / "short.mp4"
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
         "-i", str(audio), "-vf", "scale=in_range=full:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-r", str(fps), "-g", str(fps * 2),
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest", "-movflags", "+faststart", str(mp4)],
        stdin=subprocess.PIPE)
    t0 = time.time()
    for f in range(n):
        ff.stdin.write(shot(cdp, page, f / fps))
        if f % (fps * 5) == 0:
            print(f"  [render] {f}/{n} frames  ({time.time() - t0:.0f}s)", flush=True)
    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit("ERROR: ffmpeg failed while encoding")
    print(f"  [render] {n} frames done in {time.time() - t0:.0f}s")
    return mp4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--out", default="out")
    ap.add_argument("--check", action="store_true", help="voice + timing + preview sheet only (no video)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--tts", default="auto", choices=["auto", "sarvam", "edge", "gtts", "silent"],
                    help="silent = layout preview with estimated timing; only allowed with --check")
    ap.add_argument("--voice-dir", default=None, help="folder holding clips/ from scripts/get_voice.sh (Sarvam voice)")
    ap.add_argument("--min", type=float, default=50, help="target minimum seconds")
    ap.add_argument("--max", type=float, default=68, help="target maximum seconds")
    a = ap.parse_args()

    if a.tts == "silent" and not a.check:
        sys.exit("ERROR: --tts silent is for --check previews only; a video must have a voiceover.")
    sb = json.loads(Path(a.storyboard).read_text(encoding="utf-8"))
    errs, warns = validate(sb)
    for w_ in warns:
        print("WARN:", w_)
    if errs:
        sys.exit("STORYBOARD ERRORS:\n  - " + "\n  - ".join(errs))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    print("[1/4] Hindi voiceover")
    clips, eng = synth_all(sb, out, a.tts, a.voice_dir)
    tl = build_timeline(sb, clips)
    (out / "timeline.json").write_text(json.dumps(tl, indent=1))
    for i, s in enumerate(tl["scenes"]):
        print(f"   scene {i}: {s['start']:5.1f}s -> {s['end']:5.1f}s  ({s['end'] - s['start']:.1f}s, {len(s['beats'])} beats)")
    dur = tl["duration"]
    verdict = "OK" if a.min <= dur <= a.max else ("TOO LONG - trim narration" if dur > a.max else "TOO SHORT - add a beat or detail")
    print(f"   TOTAL {dur:.1f}s  [{verdict}; target {a.min:.0f}-{a.max:.0f}s]")

    print("[2/4] Audio mix")
    audio = out / "audio.wav"
    write_audio(sb, clips, tl, audio)

    print("[3/4] Layout check + preview sheet")
    from playwright.sync_api import sync_playwright
    page_path = write_page(sb, tl, out)
    with sync_playwright() as pw:
        browser, page, errors = open_page(pw, page_path)
        cdp = page.context.new_cdp_session(page)
        probs = layout_report(page, tl)
        sheet = preview_sheet(cdp, page, tl, out)
        for e in errors:
            print("   PAGE ERROR:", e)
        for p in probs:
            print("   LAYOUT:", p)
        if not probs and not errors:
            print("   layout clean")
        print(f"   preview: {sheet}")
        if a.check:
            browser.close()
            print("Check only - no video rendered. Look at the preview sheet, fix issues, then run without --check.")
            return
        print(f"[4/4] Rendering {dur:.1f}s at {a.fps} fps, frame by frame")
        mp4 = render_video(cdp, page, tl, audio, out, a.fps)
        # cover image = the hook frame once the headline has landed
        (out / "cover.jpg").write_bytes(shot(cdp, page, min(dur - .1, tl["scenes"][0]["beats"][0]["audioEnd"]), 95))
        browser.close()
    info = sh(["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "csv=p=0", str(mp4)]).stdout.decode().strip()
    print(f"DONE  {mp4}  (duration,size = {info})  voice engine: {eng}")


if __name__ == "__main__":
    main()
