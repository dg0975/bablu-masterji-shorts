#!/usr/bin/env python3
"""
Voice polish and lip-sync data for the skit characters.

polish(a, text, who, sb)  -> the clip sped up to a lively comedy pace, kid voices pitched
                             to sound like kids, cleaned (EQ + compressor) and loudness-matched
visemes(a)                -> mouth shape per video frame (openness 0..9 + shape letter)

Shape letters (drawn by lipMouth() in player.html):
  X rest/closed  M lips pressed (m/b/p)  A open "aa"  E wide "ee/e"  O round "o"  U small round "oo"  S teeth "s/f/sh"
"""
import math
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np

SR = 44100
VIS_FPS = 30

# lively but clear: syllables per second (whole clip, pauses included)
TARGET_RATE = {"golu": 6.6, "bunty": 6.3, "pinky": 6.4, "mummy": 6.4, "aunty": 6.6,
               "papa": 5.9, "dadi": 5.4, "masterji": 6.2,
               "dadaji": 5.3, "chutki": 6.4, "gupta": 6.3, "raju": 6.2}
# typical speaking pitch (Hz). Kid voices start from a light, bright voice model (Golu Zephyr, Bunty
# Erinome) and are pitched up to this with their formants (voice size) shifted too,
# so a grown-up voice model sounds like a 10-12 year old instead of a man/woman.
KID_F0 = {"golu": 275, "bunty": 262, "chutki": 300}
MAX_PAUSE = 0.14          # longest silence kept inside a line (s)


def syllables(text):
    """rough Hindi syllable count (aksharas) for Devanagari text, words for Latin text"""
    t = re.sub(r"<[^>]+>", "", text)
    n = 0
    for k, ch in enumerate(t):
        o = ord(ch)
        if 0x915 <= o <= 0x939 or 0x958 <= o <= 0x95F:
            if t[k + 1: k + 2] != "्":
                n += 1
        elif 0x905 <= o <= 0x914:
            n += 1
    if n == 0:
        n = int(len(re.findall(r"[A-Za-z]+", t)) * 1.6)
    return max(1, n)


def f0_median(a, sr=SR):
    """median speaking pitch in Hz (autocorrelation over voiced 40 ms frames); 0 if unvoiced"""
    if len(a) < sr // 5:
        return 0.0
    step = 4                                   # analyse at sr/4 for speed
    x = a[::step].astype(np.float64)
    fs = sr / step
    w, hop = int(.04 * fs), int(.01 * fs)
    lo, hi = int(fs / 500), int(fs / 75)
    rms_all = np.sqrt((x ** 2).mean()) + 1e-9
    out = []
    for s in range(0, len(x) - w, hop):
        f = x[s:s + w] - x[s:s + w].mean()
        if np.sqrt((f ** 2).mean()) < rms_all * .5:
            continue
        ac = np.correlate(f, f, "full")[w - 1:]
        if ac[0] <= 0:
            continue
        ac = ac / ac[0]
        seg = ac[lo:hi]
        k = int(np.argmax(seg))
        if seg[k] > .45:
            out.append(fs / (lo + k))
    return float(np.median(out)) if len(out) > 5 else 0.0


def squeeze_pauses(a, max_pause=MAX_PAUSE, thr=0.02):
    """trim the ends and shorten every silence inside the clip to max_pause seconds"""
    hop = SR // 100
    n = len(a) // hop
    if n < 3:
        return a
    rms = np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    loud = rms > thr * max(1e-6, rms.max())
    on = np.where(loud)[0]
    if len(on) == 0:
        return a
    keep_edge = 4
    out, run, maxgap = [], 0, int(max_pause * 100)
    for k in range(max(0, on[0] - keep_edge), min(n, on[-1] + 1 + keep_edge * 2)):
        run = 0 if loud[k] else run + 1
        if run <= maxgap:
            out.append(a[k * hop:(k + 1) * hop])
    return np.concatenate(out) if out else a


def _ffmpeg_af(a, af):
    with tempfile.TemporaryDirectory() as d:
        src, dst = Path(d) / "in.wav", Path(d) / "out.raw"
        import wave
        with wave.open(str(src), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(a, -1, 1) * 32767).astype("<i2").tobytes())
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", af, "-ac", "1", "-ar", str(SR),
                        "-f", "s16le", str(dst)], check=True, capture_output=True)
        return np.frombuffer(dst.read_bytes(), dtype=np.int16).astype(np.float32) / 32768.0


def polish(a, text, who, sb, log=None):
    """comedy-pace, character-true, clean and level voice clip"""
    cast = (sb.get("cast") or {}).get(who) or {}
    a = squeeze_pauses(a, float(sb.get("max_pause", MAX_PAUSE)))
    dur = len(a) / SR
    rate = syllables(text) / max(.3, dur)
    target = float(cast.get("rate") or TARGET_RATE.get(who, 6.2))
    tempo = min(1.32, max(1.0, target / rate))
    pitch, formant, f0 = 1.0, "preserved", 0.0
    want = cast.get("f0") or KID_F0.get(who)
    if want:
        f0 = f0_median(a)
        if f0 > 0:
            pitch = min(1.3, max(.9, float(want) / f0))
            formant = "shifted"           # smaller "voice box" too, not just higher notes
    if cast.get("pitch"):                 # manual override in semitones
        pitch, formant = 2 ** (float(cast["pitch"]) / 12), "shifted"
    chain = []
    if abs(tempo - 1) > .02 or abs(pitch - 1) > .02:
        chain.append(f"rubberband=tempo={tempo:.3f}:pitch={pitch:.3f}:formant={formant}:pitchq=quality")
    chain += ["highpass=f=85", "equalizer=f=250:t=q:w=1.2:g=-2", "equalizer=f=3300:t=q:w=1.4:g=3",
              "acompressor=threshold=0.09:ratio=3:attack=4:release=80:makeup=1.6"]
    try:
        a = _ffmpeg_af(a, ",".join(chain))
    except Exception as e:  # noqa  (keep the raw clip rather than fail the video)
        if log:
            log(f"  [voice] polish failed for {who}: {e}")
    # loudness match: every character at the same speech level
    hop = SR // 100
    n = len(a) // hop
    if n:
        rms = np.sqrt((a[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
        sp = rms[rms > rms.max() * .1]
        lvl = float(np.sqrt((sp ** 2).mean())) if len(sp) else 0
        if lvl > 0:
            a = a * (0.11 / lvl)
        pk = np.abs(a).max()
        if pk > .97:
            a = np.tanh(a / pk * 1.4) / np.tanh(1.4) * .97
    if log:
        log(f"  [voice] {who:<8} {rate:4.1f} syl/s -> x{tempo:.2f}" + (f"  pitch {f0:.0f}Hz x{pitch:.2f}" if want else "") +
            f"  {dur:.2f}s -> {len(a) / SR:.2f}s")
    return a.astype(np.float32)


def visemes(a, fps=VIS_FPS):
    """per video frame: (openness 0..9, shape letter), led by one frame so the mouth anticipates the sound"""
    hop = SR // fps
    win = hop * 2
    n = len(a) // hop + 1
    pad = np.concatenate([np.zeros(win // 2, np.float32), a, np.zeros(win, np.float32)])
    freqs = np.fft.rfftfreq(win, 1 / SR)
    band = lambda lo, hi: (freqs >= lo) & (freqs < hi)  # noqa
    B1, B2, B3, B4 = band(150, 900), band(900, 2400), band(2400, 4500), band(4500, 10000)
    han = np.hanning(win)
    rms, feat = np.zeros(n), []
    for k in range(n):
        f = pad[k * hop: k * hop + win] * han
        rms[k] = np.sqrt((f ** 2).mean())
        sp = np.abs(np.fft.rfft(f)) ** 2
        e1, e2, e3, e4 = sp[B1].sum(), sp[B2].sum(), sp[B3].sum(), sp[B4].sum()
        tot = e1 + e2 + e3 + e4 + 1e-12
        feat.append((e1 / tot, (e2 + e3) / tot, e4 / tot))
    ref = np.percentile(rms[rms > 1e-4], 90) if (rms > 1e-4).any() else 1
    op = np.clip(rms / max(ref, 1e-6), 0, 1.15) ** .65
    voiced = [k for k in range(n) if op[k] >= .1]
    med = np.median(np.array([feat[k] for k in voiced]), axis=0) if voiced else np.array([.6, .35, .05])
    shapes = []
    for k in range(n):
        lo_, mid, hi_ = feat[k]
        o = op[k]
        if o < .1:
            s = "X"
        elif (hi_ > .3 or hi_ - med[2] > .18) and o < .8:
            s = "S"
        elif lo_ - med[0] > .07:
            s = "O" if o > .55 else "U"
        elif mid - med[1] > .06:
            s = "E"
        else:
            s = "A"
        shapes.append(s)
    # a short dip inside speech is a closed-lip consonant (m, b, p)
    for k in range(1, n - 1):
        if shapes[k] == "X" and shapes[k - 1] not in "XM" and k + 2 < n and shapes[k + 1] != "X":
            shapes[k] = "M"
    # no single-frame flicker
    for k in range(1, n - 1):
        if shapes[k - 1] == shapes[k + 1] != shapes[k] and shapes[k] not in "MX":
            shapes[k] = shapes[k - 1]
    o9 = [int(round(min(1, v) * 9)) if s not in "XM" else 0 for v, s in zip(op, shapes)]
    return o9[1:] + [0], shapes[1:] + ["X"]
