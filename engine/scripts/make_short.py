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
VTYPES = {"svg", "html", "cards", "bars", "list", "number", "compare", "3d"}


def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, **kw)


def pip_install(pkg):
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", pkg],
                   check=False, capture_output=True)


# ----------------------------------------------------------------------------- validation
SKIT_CAST = {"masterji", "golu", "mummy", "papa", "dadi", "pinky", "bunty", "aunty"}
SKIT_SETS = {"classroom", "livingroom", "kitchen", "train", "tapri", "terrace", "bedroom"}
SKIT_POSES = {"idle", "talk", "shock", "happy", "laugh", "angry", "sad", "point", "think", "sly", "dance", "hand", "facepalm", "hold", "wave"}
SKIT_FX = {"bulb", "sweat", "question", "stars", "anger", "hearts", "pop", "lines"}
SFX_NAMES = {"boing", "ding", "whoosh", "drum", "pop", "crash", "bell", "slide", "scratch"}


def validate_skit(sb):
    errs, warns = [], []
    scenes = sb.get("scenes") or []
    if not scenes:
        errs.append("skit has no scenes (shots)")
    for i, s in enumerate(scenes):
        tag = f"shot {i}"
        if s.get("set", "classroom") not in SKIT_SETS:
            errs.append(f"{tag}: unknown set {s.get('set')!r} (use {sorted(SKIT_SETS)})")
        ids = [c.get("id") for c in s.get("cast", [])]
        for c in ids:
            if c not in SKIT_CAST:
                errs.append(f"{tag}: unknown character {c!r} (use {sorted(SKIT_CAST)})")
        for j, b in enumerate(s.get("beats") or []):
            if b.get("who") and b["who"] not in ids:
                errs.append(f"{tag} beat {j}: speaker {b['who']!r} is not in this shot's cast")
            for c, pose in (b.get("act") or {}).items():
                if c not in ids:
                    errs.append(f"{tag} beat {j}: act for {c!r}, who is not in the shot")
                if pose not in SKIT_POSES:
                    errs.append(f"{tag} beat {j}: unknown pose {pose!r} (use {sorted(SKIT_POSES)})")
            for f in [] if not b.get("fx") else (b["fx"] if isinstance(b["fx"], list) else [b["fx"]]):
                if f.get("kind") not in SKIT_FX:
                    errs.append(f"{tag} beat {j}: unknown fx {f.get('kind')!r} (use {sorted(SKIT_FX)})")
            for x in [] if not b.get("sfx") else (b["sfx"] if isinstance(b["sfx"], list) else [b["sfx"]]):
                name = x if isinstance(x, str) else x.get("s")
                if name not in SFX_NAMES:
                    errs.append(f"{tag} beat {j}: unknown sfx {name!r} (use {sorted(SFX_NAMES)})")
            if not b.get("say") and not b.get("hold"):
                warns.append(f"{tag} beat {j}: no line and no 'hold'; using 1.2 s")
    return errs, warns


def validate(sb):
    if sb.get("kind") == "skit":
        return validate_skit(sb)
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


def trim_silence(a, thr=0.012, keep=0.06):
    """cut long silence at the start/end of a clip and squeeze long pauses inside it to 0.35 s"""
    import numpy as np
    if len(a) == 0:
        return a
    hop = SR // 100
    n = len(a) // hop
    if n < 3:
        return a
    rms = np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    on = np.where(rms > thr * max(1e-6, rms.max()) * 8)[0]
    if len(on) == 0:
        return a
    s0 = max(0, on[0] * hop - int(keep * SR)); s1 = min(len(a), (on[-1] + 1) * hop + int(keep * SR))
    a = a[s0:s1]; rms = rms[on[0]:on[-1] + 1]
    out, run, maxgap = [], 0, int(.35 * 100)
    loud = rms > thr * max(1e-6, rms.max()) * 8
    for k in range(len(rms)):
        run = 0 if loud[k] else run + 1
        if run <= maxgap:
            out.append(a[k * hop:(k + 1) * hop])
    return np.concatenate(out) if out else a


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
        c = st.beat_cfg(sb, i, j)
        f = cdir / f"{st.clip_key(c, text)}.wav"
        if not f.exists() and c.get("engine") == "gemini" and os.environ.get("GEMINI_API_KEY"):
            import gemini_tts
            gemini_tts.synth(text, c["voice"], c["style"], os.environ["GEMINI_API_KEY"].strip(), str(f))
        elif not f.exists() and api_key and c.get("engine") != "gemini":
            st.synth(text, c, api_key, str(f))
        if f.exists():
            if sb.get("kind") == "skit":           # comedy pace, kid voices that sound like kids, level and clean
                import voice_fx
                who = sb["scenes"][i]["beats"][j].get("who", "")
                clips[(i, j)] = voice_fx.polish(load_pcm(f), text, who, sb, log=print)
            else:
                clips[(i, j)] = trim_silence(load_pcm(f))
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
    skit = sb.get("kind") == "skit"
    gap, lead = float(sb.get("gap", 0.28)), float(sb.get("lead", 0.5))
    if skit:                       # snappy: lines follow each other like real banter, reactions stay short
        gap, lead = min(gap, 0.08), min(lead, 0.12)
    t, scenes = 0.0, []
    for i, s in enumerate(sb["scenes"]):
        st = t
        t += lead
        beats = []
        for j, b in enumerate(s["beats"]):
            d = len(clips[(i, j)]) / SR if (i, j) in clips else float(b.get("hold", 1.2))
            if skit and (i, j) not in clips:
                d = min(d, 0.75)
            extra = float(b.get("pause", 0))
            beats.append({"start": round(t, 3), "audioEnd": round(t + d, 3), "end": round(t + d + gap + extra, 3)})
            t += d + gap + extra
        t += 0.04 if skit else 0.15
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


def music_lively(n, seed=1, bpm=None):
    """upbeat original background tune, generated in code (no samples, no copyright):
    light beat + tabla-style taps + bouncy bass + sitar-like plucked melody over I-V-vi-IV chords"""
    import numpy as np
    R = np.random.default_rng(seed)
    bpm = bpm or int(R.choice([100, 104, 108, 112]))
    beat = 60.0 / bpm; s16 = beat / 4
    key = float(R.choice([0, 2, 5, 7, -3]))                       # C, D, F, G, A major
    f = lambda semi: 261.63 * 2 ** ((semi + key) / 12)               # semitones from C4 (+key)
    out = np.zeros(n + SR * 2, dtype=np.float32)
    dur = n / SR

    def put(sig, t, gain):
        a = int(t * SR); b = min(len(out), a + len(sig))
        if a < len(out): out[a:b] += sig[: b - a] * gain

    def env(L, a=.004, d=.2):
        t = np.arange(int(L * SR)) / SR
        return np.minimum(t / a, 1) * np.exp(-t / d)

    def pluck(freq, L=.55, bright=1.0, bend=0.0):
        t = np.arange(int(L * SR)) / SR
        fr = freq * (1 + bend * np.exp(-t * 18))                  # small "meend" slide into the note
        ph = 2 * np.pi * np.cumsum(fr) / SR
        sig = sum((1 / k) * np.exp(-t * (3 + k * 2.2 / bright)) * np.sin(k * ph + k) for k in range(1, 9))
        sig += .18 * np.exp(-t * 9) * np.sin(13 * ph)              # bright "jawari" buzz
        return sig * np.minimum(t / .003, 1)

    def kick():
        t = np.arange(int(.22 * SR)) / SR
        return np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-t * 30)) / SR) * np.exp(-t * 14)

    noise = R.standard_normal(SR).astype(np.float32)
    def hat(L=.035):
        x = noise[: int(L * SR)].copy(); x = np.diff(x, prepend=0)     # crude high-pass
        return x * np.exp(-np.arange(len(x)) / SR / (L / 4))
    def clap():
        x = noise[: int(.14 * SR)] * env(.14, .002, .045)
        return np.convolve(x, np.ones(3) / 3, 'same')
    def tabla(high=True):
        t = np.arange(int(.18 * SR)) / SR
        f0 = (330 if high else 150) * (1 + .25 * np.exp(-t * 40))
        return np.sin(2 * np.pi * np.cumsum(f0) / SR) * np.exp(-t * (22 if high else 12))

    prog = [(0, 4, 7), (7, 11, 14), (9, 12, 16), (5, 9, 12)]          # I  V  vi  IV
    scale = [0, 2, 4, 7, 9, 12, 14, 16]                                 # major pentatonic (+octave)
    motif = [int(x) for x in R.choice(len(scale), 8)]                   # this video's hook phrase
    rhythm = [0, 3, 6, 8, 10, 11, 14, 15]                               # 16th positions in a bar
    tab_pat = [1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 1, 0]
    bar = beat * 4; nbars = int(np.ceil(dur / bar)) + 1
    for b in range(nbars):
        t0 = b * bar; root, third, fifth = prog[b % 4]
        sec = (b // 4) % 4                                              # 4-bar sections: build up, full, full, light
        for q in range(4):                                              # beat layer
            tq = t0 + q * beat
            if sec > 0 or q in (0, 2): put(kick(), tq, .9 if q in (0, 2) else .45)
            if q in (1, 3) and sec > 0: put(clap(), tq, .32)
        for e in range(8):                                              # swung shaker on 8ths
            put(hat(), t0 + e * beat / 2 + (s16 * .33 if e % 2 else 0), .12 if e % 2 else .07)
        for k in range(16):                                             # tabla-style taps
            if tab_pat[(k + b) % 16] and sec != 0: put(tabla(k % 4 != 0), t0 + k * s16, .22)
        for e, semi in enumerate([root, root, root + 12, root, fifth, root, root + 12, fifth]):   # bouncy bass
            put(pluck(f(semi - 24), .32, .6), t0 + e * beat / 2, .55)
        for v in (root, third, fifth):                                  # soft chord stabs on the off-beats
            for q in range(4):
                put(pluck(f(v), .3, .5), t0 + q * beat + beat / 2, .07)
        if sec in (1, 2):                                               # sitar-like hook melody
            for i, pos in enumerate(rhythm):
                note = scale[(motif[i] + (b % 2) * (i % 3 == 0)) % len(scale)]
                put(pluck(f(note + 12), .5, 1.3, bend=.03 if i % 3 == 0 else 0), t0 + pos * s16, .26)
    out = out[:n]
    out = out / max(1e-6, np.sqrt((out ** 2).mean())) * 0.25          # loudness-normalise (RMS), not peak
    return np.tanh(out * 1.6) / 1.6                                    # soft limiter keeps the kick from spiking


def _synth_kit(R, n):
    """shared helpers for the code-made background tunes"""
    import numpy as np
    out = np.zeros(n + SR * 2, dtype=np.float32)
    noise = R.standard_normal(SR).astype(np.float32)
    K = {}
    def put(sig, t, gain):
        a = int(t * SR); b = min(len(out), a + len(sig))
        if 0 <= a < len(out): out[a:b] += sig[: b - a] * gain
    def tt(L): return np.arange(int(L * SR)) / SR
    def kick(soft=False):
        t = tt(.25); return np.sin(2 * np.pi * np.cumsum(48 + (60 if soft else 90) * np.exp(-t * 30)) / SR) * np.exp(-t * (10 if soft else 14))
    def snare(L=.16, tone=190):
        t = tt(L); x = noise[: len(t)] * np.exp(-t / (L / 4)); x = np.convolve(x, np.ones(4) / 4, 'same')
        return .7 * x + .4 * np.sin(2 * np.pi * tone * t) * np.exp(-t * 30)
    def hat(L=.035, g=1.0):
        x = np.diff(noise[: int(L * SR)], prepend=0); return x * np.exp(-tt(L) / (L / 4)) * g
    def epiano(freq, L=1.6):
        t = tt(L); trem = 1 + .25 * np.sin(2 * np.pi * 5 * t)
        sig = np.sin(2 * np.pi * freq * t + .8 * np.exp(-t * 3) * np.sin(2 * np.pi * freq * 2 * t))
        return sig * np.exp(-t * 1.6) * np.minimum(t / .01, 1) * trem
    def marimba(freq, L=.35):
        t = tt(L); return (np.sin(2 * np.pi * freq * t) + .3 * np.sin(2 * np.pi * freq * 3.9 * t) * np.exp(-t * 40)) * np.exp(-t * 11) * np.minimum(t / .002, 1)
    def whistle(freq, L=.3):
        t = tt(L); ph = 2 * np.pi * np.cumsum(freq * (1 + .012 * np.sin(2 * np.pi * 6 * t))) / SR
        return np.sin(ph) * np.minimum(t / .03, 1) * np.minimum((L - t) / .05, 1)
    def bass(freq, L=.3, bright=.6):
        t = tt(L); ph = 2 * np.pi * freq * t
        return sum((1 / k) * np.exp(-t * (3 + k * 2.2 / bright)) * np.sin(k * ph) for k in range(1, 6)) * np.minimum(t / .004, 1)
    K.update(put=put, kick=kick, snare=snare, hat=hat, epiano=epiano, marimba=marimba, whistle=whistle, bass=bass, noise=noise)
    return out, K


def music_lofi(n, seed=1):
    """calm lo-fi: lazy swung drums, warm electric-piano 7th chords, soft melody, vinyl crackle"""
    import numpy as np
    R = np.random.default_rng(seed); out, K = _synth_kit(R, n); put = K["put"]
    bpm = int(R.choice([80, 84, 88])); beat = 60 / bpm; key = float(R.choice([0, 2, 5, -3, -5]))
    f = lambda s: 261.63 * 2 ** ((s + key) / 12)
    prog = [(0, 4, 7, 11), (9, 12, 16, 19), (2, 5, 9, 12), (7, 11, 14, 17)]     # Imaj7 vi7 ii7 V7
    scale = [0, 2, 4, 7, 9, 12, 14]; motif = [int(x) for x in R.choice(len(scale), 6)]
    bar = beat * 4
    for b in range(int(np.ceil(n / SR / bar)) + 1):
        t0 = b * bar; ch = prog[b % 4]
        for q in range(4):
            if q in (0,) or (q == 2 and b % 2): put(K["kick"](soft=True), t0 + q * beat + (beat * .05 if q else 0), .8)
            if q in (1, 3): put(K["snare"](.2, 170), t0 + q * beat + beat * .03, .28)
        for e in range(8): put(K["hat"](.03, .7), t0 + e * beat / 2 + (beat / 6 if e % 2 else 0), .08 if e % 2 else .05)
        for v in ch: put(K["epiano"](f(v), bar * .95), t0 + .02 * (v % 3), .11)
        put(K["bass"](f(ch[0] - 24), beat * 1.6), t0, .6); put(K["bass"](f(ch[2] - 24), beat * 1.2), t0 + beat * 2.5, .45)
        if (b // 4) % 2 == 1:
            for i, pos in enumerate([0, 1.5, 2, 3, 3.5, 5][: len(motif)]):
                put(K["epiano"](f(scale[motif[i]] + 12), .7), t0 + pos * beat / 1.5, .12)
    crackle = (np.abs(R.standard_normal(len(out))) > 3.6) * R.standard_normal(len(out)) * .25
    out += crackle.astype(np.float32) * .15
    out = out[:n]; out = out / max(1e-6, np.sqrt((out ** 2).mean())) * 0.25
    return np.tanh(out * 1.6) / 1.6


def music_funky(n, seed=1):
    """playful quiz-show groove: tight claps, walking bass, marimba riff, whistle hook"""
    import numpy as np
    R = np.random.default_rng(seed); out, K = _synth_kit(R, n); put = K["put"]
    bpm = int(R.choice([116, 120, 124])); beat = 60 / bpm; key = float(R.choice([0, 2, 5, 7]))
    f = lambda s: 261.63 * 2 ** ((s + key) / 12)
    prog = [(0, 4, 7), (5, 9, 12), (7, 11, 14), (5, 9, 12)]                       # I IV V IV
    walk = [0, 4, 7, 9]; riff = [0, 7, 4, 9, 7, 12, 9, 7]; hook = [int(x) for x in R.choice([0, 2, 4, 7, 9, 12], 5)]
    bar = beat * 4
    for b in range(int(np.ceil(n / SR / bar)) + 1):
        t0 = b * bar; root = prog[b % 4][0]; sec = (b // 4) % 3
        for q in range(4):
            put(K["kick"](), t0 + q * beat, .7 if q in (0, 2) else .35)
            if q in (1, 3): put(K["snare"](.12, 220), t0 + q * beat, .3)
        for e in range(16):
            if e % 2 or sec: put(K["hat"](.02, 1), t0 + e * beat / 4, .07)
        for e, w in enumerate(walk): put(K["bass"](f(root + w - 24), beat * .9, .9), t0 + e * beat, .55)
        for e, r in enumerate(riff): put(K["marimba"](f(root + r)), t0 + e * beat / 2 + (beat / 4 if e % 3 == 2 else 0), .16)
        if sec == 1:
            for i, h in enumerate(hook): put(K["whistle"](f(h + 12), beat * .45), t0 + i * beat * .75, .1)
    out = out[:n]; out = out / max(1e-6, np.sqrt((out ** 2).mean())) * 0.25
    return np.tanh(out * 1.6) / 1.6


MUSIC_STYLES = ["desi", "lofi", "funky"]


def music_for(sb, n):
    """pick the tune: storyboard music_style (funky default | desi | lofi | rotate = by date)"""
    import datetime, zlib
    style = sb.get("music_style", "funky")
    if style in ("rotate", "lively"):
        if style == "lively": style = "desi"
        else: style = MUSIC_STYLES[datetime.date.today().toordinal() % len(MUSIC_STYLES)]
    seed = zlib.crc32((sb.get("title") or "x").encode())
    fn = {"desi": music_lively, "lofi": music_lofi, "funky": music_funky}[style]
    print(f"  [music] style: {style}")
    return fn(n, seed=seed), style


def sfx(name):
    """small comedy sound effects made in code (no samples)"""
    import numpy as np
    t = lambda L: np.arange(int(L * SR)) / SR
    R = np.random.default_rng(len(name))
    if name == "boing":
        x = t(.6); f = 180 + 220 * np.exp(-x * 6) * (1 + .5 * np.sin(2 * np.pi * 14 * x))
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 4) * .9
    if name == "ding":
        x = t(1.2); return (np.sin(2 * np.pi * 1320 * x) + .5 * np.sin(2 * np.pi * 2640 * x) + .3 * np.sin(2 * np.pi * 3960 * x)) * np.exp(-x * 3.5) * .45
    if name == "whoosh":
        x = t(.5); n = R.standard_normal(len(x)); k = int(SR * .002); n = np.convolve(n, np.ones(k) / k, "same")
        return n * np.sin(np.pi * x / .5) ** 2 * 1.4
    if name == "pop":
        x = t(.12); return np.sin(2 * np.pi * np.cumsum(900 - 5000 * x) / SR) * np.exp(-x * 40) * .8
    if name == "crash":
        x = t(1.0); return R.standard_normal(len(x)) * np.exp(-x * 4) * .5
    if name == "drum":   # ba-dum-tss
        out = np.zeros(int(1.3 * SR))
        for at, f0 in ((0, 180), (.18, 140)):
            x = t(.25); a = int(at * SR); out[a:a + len(x)] += np.sin(2 * np.pi * f0 * x * (1 + .3 * np.exp(-x * 30))) * np.exp(-x * 14) * .8
        x = t(.9); a = int(.38 * SR); hi = np.diff(R.standard_normal(len(x) + 1)); out[a:a + len(x)] += hi * np.exp(-x * 5) * .35
        return out
    if name == "bell":   # school bell ring
        x = t(1.4); trem = (np.sign(np.sin(2 * np.pi * 22 * x)) + 1) / 2
        return (np.sin(2 * np.pi * 1700 * x) + .6 * np.sin(2 * np.pi * 2350 * x)) * trem * np.exp(-x * 1.2) * .35
    if name == "slide":  # slide whistle down
        x = t(.7); f = 1400 * np.exp(-x * 2.2) + 300
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(x / .03, 1) * np.exp(-x * 1.5) * .5
    if name == "scratch":
        x = t(.35); f = 300 + 900 * np.abs(np.sin(2 * np.pi * 6 * x))
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * .5 + R.standard_normal(len(x)) * .25) * np.exp(-x * 4)
    return np.zeros(1)


def duck_curve(voice, depth=0.5):
    """gain curve that lowers the music while the voice speaks (smooth attack/release)"""
    import numpy as np
    hop = SR // 100
    n = len(voice) // hop + 1
    rms = np.array([np.sqrt((voice[i * hop:(i + 1) * hop] ** 2).mean()) if i * hop < len(voice) else 0 for i in range(n)])
    act = (rms > 0.02).astype(float)
    g = np.ones(n)
    for i in range(1, n):                      # fast duck (60 ms), slow return (400 ms)
        target = 1 - depth * act[i]
        k = 0.17 if target < g[i - 1] else 0.025
        g[i] = g[i - 1] + (target - g[i - 1]) * k
    return np.interp(np.arange(len(voice)) / hop, np.arange(n), g).astype(np.float32)


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
    try:                                          # mouth shapes per frame for lip-sync
        import voice_fx
        nf = int(tl["duration"] * voice_fx.VIS_FPS) + 2
        vo, vs = [0] * nf, ["X"] * nf
        for (i, j), a in clips.items():
            o9, shp = voice_fx.visemes(a)
            f0 = int(round(tl["scenes"][i]["beats"][j]["start"] * voice_fx.VIS_FPS))
            for k in range(len(o9)):
                if 0 <= f0 + k < nf:
                    vo[f0 + k], vs[f0 + k] = o9[k], shp[k]
        tl["visO"], tl["visS"], tl["visFps"] = vo, "".join(vs), voice_fx.VIS_FPS
    except Exception as e:  # noqa
        print(f"  [lipsync] skipped: {e}")
    style = sb.get("music_style", "funky")
    vol = sb.get("music", 0.05 if style == "pad" else 0.2)
    if vol:
        vol = float(vol if vol is not True else (0.05 if style == "pad" else 0.2))
        if style == "pad":
            bed = music_bed(n) * vol
        else:
            tune, style = music_for(sb, n)
            bed = tune * vol * duck_curve(mix, float(sb.get("duck", 0.5)))
        tl["music_style"] = style
        fade = int(.8 * SR)
        bed[:fade] *= np.linspace(0, 1, fade)
        bed[-fade:] *= np.linspace(1, 0, fade)
        mix += bed
    for i, s in enumerate(sb["scenes"]):          # comedy sound effects at their beats
        for j, b in enumerate(s.get("beats", [])):
            fxl = b.get("sfx")
            if not fxl:
                continue
            for x in (fxl if isinstance(fxl, list) else [fxl]):
                name, at, g = (x, 0.0, 1.0) if isinstance(x, str) else (x.get("s"), float(x.get("at", 0)), float(x.get("gain", 1)))
                a = sfx(name).astype(np.float32) * 0.6 * g
                st_ = int((tl["scenes"][i]["beats"][j]["start"] + at) * SR)
                e = min(n, st_ + len(a))
                if 0 <= st_ < n:
                    mix[st_:e] += a[: e - st_]
    mix = np.clip(mix, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix * 32767).astype("<i2").tobytes())


# ----------------------------------------------------------------------------- rendering
def write_page(sb, tl, out):
    html = (ASSETS / "player.html").read_text(encoding="utf-8")
    if sb.get("kind") == "skit":                  # skits reuse Masterji's drawing code from the player
        a = html.index("/* ---------------- Bablu Masterji"); b = html.index("/* ---------------- build")
        html = (ASSETS / "skit.html").read_text(encoding="utf-8").replace("/*MASTERJI*/", html[a:b])
    fdir = (ASSETS / "fonts").resolve()
    faces = "".join(
        f"@font-face{{font-family:'Poppins';font-weight:{wgt};src:url('file://{fdir}/Poppins-{name}.ttf')}}\n"
        for wgt, name in ((400, "Regular"), (500, "Medium"), (700, "Bold")) if (fdir / f"Poppins-{name}.ttf").exists())
    if (fdir / "Kalam-Bold.ttf").exists():
        faces += f"@font-face{{font-family:'Kalam';font-weight:700;src:url('file://{fdir}/Kalam-Bold.ttf')}}\n"
    data = "const SB=" + json.dumps(sb, ensure_ascii=False).replace("</", "<\\/") + ";\nconst TL=" + json.dumps(tl) + ";"
    libs = ""
    if sb.get("kind") != "skit" and any((sc.get("visual") or {}).get("type") == "3d" for sc in sb["scenes"]):
        for js in (ASSETS / "vendor" / "three.min.js", ASSETS / "g3d.js"):
            libs += f'<script src="file://{js.resolve()}"></script>\n'
    html = html.replace("/*FONTS*/", faces).replace("<script>\n/*DATA*/", libs + "<script>\n/*DATA*/", 1).replace("/*DATA*/", data)
    page = out / "_page.html"
    page.write_text(html, encoding="utf-8")
    return page


def open_page(pw, page_path):
    try:
        browser = pw.chromium.launch(args=["--force-color-profile=srgb", "--font-render-hinting=none", "--disable-lcd-text",
                                          "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
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
    if page.evaluate("typeof SB!=='undefined' && SB.kind==='skit'"):
        return []
    js = """(t)=>{window.NOCAM=true; renderAt(t); window.NOCAM=false; const out=[]; const sc=[...document.querySelectorAll('.scene')].find(e=>e.style.display==='block');
      const v=sc.querySelector('.visual').getBoundingClientRect(), h=sc.querySelector('.head').getBoundingClientRect();
      if(h.bottom>592) out.push('header text runs into the visual by '+Math.round(h.bottom-592)+'px (shorten headline/sub)');
      for(const el of sc.querySelectorAll('.visual .c-fill > *')){if(+getComputedStyle(el).opacity<0.05) continue; const r=el.getBoundingClientRect();
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
