"""
Finish a skit made in Google Flow: join the clips, add the channel look (hook, series badge, subtitles,
handle, science end card) and write a post-ready MP4 + cover.

Usage: python3 scripts/flow_finish.py flow/<name>.json [--out work_flow/<name>]
flow/<name>.json:
 {"clips": ["flow/<name>/1.mp4", ...],            # in order; any size/fps, re-framed to 1080x1920 30 fps
  "trim": [[0.0, 8.0], ...],                       # optional seconds to keep per clip
  "hook": "Chammach ne *kaata*? 😱", "series": "MUMMY KA RULE · PART 1", "title": "Chammach ne kaata?",
  "handle": "@bablu.masterji",
  "lines": [{"start": 0.2, "end": 2.0, "speaker": "Golu", "text": "आह! ..."}],   # from transcribe/<name>.json
  "card": {"kicker": "Science ka sach", "text": "...", "foot": "..."}, "card_secs": 2.6}
Subtitle times are seconds in the joined video (before the end card).
"""
import json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "engine" / "assets" / "fonts"
W, H, FPS = 1080, 1920, 30
TAG = {"masterji": "#ffd54a", "golu": "#8fd3ff", "mummy": "#ff9ac2", "papa": "#c6f08a", "dadi": "#f3efe4", "pinky": "#ffb3d1",
       "bunty": "#d6c8ff", "aunty": "#9ff0c4", "sharma aunty": "#9ff0c4", "dadaji": "#e6e2da", "chutki": "#ffd54a",
       "gupta": "#ffc27a", "gupta uncle": "#ffc27a", "raju": "#9fe0d0", "raju bhaiya": "#9fe0d0"}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("ERROR: " + " ".join(map(str, cmd[:6])) + "\n" + r.stderr[-1500:])
    return r.stdout


def dur(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).strip())


def has_audio(p):
    return "audio" in run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(p)])


OVERLAY = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
@font-face{font-family:Poppins;font-weight:700;src:url('file://FONTS/Poppins-Bold.ttf')}
@font-face{font-family:Poppins;font-weight:500;src:url('file://FONTS/Poppins-Medium.ttf')}
html,body{margin:0;width:1080px;height:1920px;background:transparent;overflow:hidden;font-family:Poppins,'Noto Sans Devanagari',sans-serif}
#hook{position:absolute;left:50px;right:50px;top:300px;text-align:center;font-weight:700;font-size:86px;line-height:1.08;color:#fff;
 -webkit-text-stroke:10px #1e1620;paint-order:stroke fill;text-shadow:0 10px 0 #1e1620,0 0 30px rgba(0,0,0,.5);transform-origin:50% 50%}
#hook b{color:#ffd54a}
#title{position:absolute;left:40px;top:150px;display:flex;flex-direction:column;gap:6px}
#title .series{align-self:flex-start;background:#ffd54a;color:#1e1620;font-weight:700;font-size:30px;letter-spacing:.06em;padding:8px 22px;border-radius:30px;border:4px solid #1e1620}
#title .ep{color:#fff;font-weight:700;font-size:40px;text-shadow:0 4px 0 #1e1620,0 0 14px rgba(0,0,0,.6)}
#handle{position:absolute;right:40px;top:160px;color:#fff;font-weight:700;font-size:30px;text-shadow:0 3px 0 #1e1620}
#sub{position:absolute;left:60px;right:60px;top:1452px;display:flex;flex-direction:column;align-items:center;gap:8px}
#sub .who{font-weight:700;font-size:32px;padding:4px 20px;border-radius:24px;border:3px solid #1e1620;color:#1e1620}
#sub .line{background:rgba(14,14,22,.86);color:#fff;font-weight:700;font-size:46px;line-height:1.35;text-align:center;padding:14px 30px;border-radius:26px;max-width:960px}
#card{position:absolute;left:70px;right:70px;top:640px;background:#fffaf0;border:6px solid #1e1620;border-radius:40px;padding:44px 50px;box-shadow:0 18px 0 #1e1620;text-align:center}
#card .k{display:inline-block;background:#2bd67b;color:#0b2416;font-weight:700;font-size:34px;padding:6px 24px;border-radius:26px;margin-bottom:22px}
#card .t{color:#1e1620;font-weight:700;font-size:52px;line-height:1.3}
#card .f{margin-top:26px;color:#7a5a2e;font-weight:700;font-size:36px}
</style></head><body><div id="hook"></div><div id="title"><div class="series"></div><div class="ep"></div></div><div id="handle"></div>
<div id="sub"><div class="who"></div><div class="line"></div></div><div id="card"><div class="k"></div><div class="t"></div><div class="f"></div></div>
<script>
const C=CONF, $=s=>document.querySelector(s), clamp=(x,a=0,b=1)=>Math.max(a,Math.min(b,x)), eOut=p=>1-Math.pow(1-clamp(p),3);
$('#hook').innerHTML=(C.hook||'').replace(/[<>&]/g,'').replace(/\*([^*]+)\*/g,'<b>$1</b>');
$('.series').textContent=C.series||''; $('.ep').textContent=C.title||''; $('#handle').textContent=C.handle||'@bablu.masterji';
$('#card .k').textContent=(C.card||{}).kicker||'Science ka sach'; $('#card .t').textContent=(C.card||{}).text||''; $('#card .f').textContent=(C.card||{}).foot||'';
window.frameAt=t=>{const hu=C.hook_until||2.6, endT=C.main_dur;
 const hk=$('#hook'); if(!C.hook||t>hu+.3) hk.style.opacity=0; else {const o=t<hu?1:1-(t-hu)/.3, sc=1+.06*Math.sin(Math.min(1,t/.5)*Math.PI)+.015*Math.sin(t*7);
   hk.style.opacity=o.toFixed(3); hk.style.transform=`scale(${sc.toFixed(3)}) rotate(${(-1.5+Math.sin(t*3)*.6).toFixed(2)}deg)`}
 $('#title').style.opacity=(C.hook&&t<hu)?0:1;
 const L=(C.lines||[]).find(l=>t>=l.start&&t<=l.end+.15&&t<endT);
 $('#sub').style.opacity=L?1:0;
 if(L){const w=$('#sub .who'); w.textContent=L.speaker||''; w.style.display=L.speaker?'block':'none'; w.style.background=C.tags[(L.speaker||'').toLowerCase()]||'#fff'; $('#sub .line').textContent=L.text}
 const c=$('#card'), lt=t-endT; if(lt<0) c.style.opacity=0; else {c.style.opacity=clamp(lt/.3); c.style.transform=`translateY(${((1-eOut(lt/.45))*60).toFixed(1)}px)`}
};
window.__ready=true;
</script></body></html>"""


def main():
    cfg_path = Path(sys.argv[1])
    C = json.loads(cfg_path.read_text())
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else ROOT / "work_flow" / cfg_path.stem
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())
    # 1) re-frame every clip to 1080x1920 30 fps with stereo audio, then join
    parts = []
    for i, c in enumerate(C["clips"]):
        src = (ROOT / c) if not Path(c).is_absolute() else Path(c)
        tr = (C.get("trim") or [None] * len(C["clips"]))[i]
        cut = ["-ss", str(tr[0]), "-to", str(tr[1])] if tr else []
        p = tmp / f"p{i}.mp4"
        audio = [] if has_audio(src) else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
        run(["ffmpeg", "-y", "-v", "error", *cut, "-i", str(src), *audio,
             "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS},setsar=1",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-c:a", "aac", "-ar", "48000", "-ac", "2",
             *([] if not audio else ["-shortest", "-map", "0:v", "-map", "1:a"]), str(p)])
        parts.append(p)
    lst = tmp / "list.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
    joined = tmp / "joined.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])
    main_dur = dur(joined)
    # 2) end card tail: the last frame, softly blurred and dimmed
    card_secs = float(C.get("card_secs", 2.6)) if C.get("card") else 0
    full = tmp / "full.mp4"
    if card_secs:
        run(["ffmpeg", "-y", "-v", "error", "-i", str(joined), "-filter_complex",
             f"[0:v]tpad=stop_mode=clone:stop_duration={card_secs}[v0];[v0]split[a][b];[b]trim=start={main_dur},setpts=PTS-STARTPTS,boxblur=18:2,eq=brightness=-0.08[bl];"
             f"[a]trim=end={main_dur},setpts=PTS-STARTPTS[m];[m][bl]concat=n=2:v=1:a=0[v];[0:a]apad=pad_dur={card_secs}[au]",
             "-map", "[v]", "-map", "[au]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-c:a", "aac", "-t", str(main_dur + card_secs), str(full)])
    else:
        full = joined
    total = dur(full)
    # 3) overlay frames (hook, badge, subtitles, card) rendered in Chromium and composited
    conf = dict(C, main_dur=main_dur, tags=TAG)
    page = tmp / "overlay.html"
    page.write_text(OVERLAY.replace("FONTS", str(FONTS.resolve())).replace("CONF", json.dumps(conf, ensure_ascii=False)), encoding="utf-8")
    final = out / "short.mp4"
    from playwright.sync_api import sync_playwright
    n = int(total * FPS)
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-i", str(full), "-f", "image2pipe", "-framerate", str(FPS), "-c:v", "png", "-i", "-",
                           "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];[0:a]loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                           "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-r", str(FPS),
                           "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-movflags", "+faststart", "-shortest", str(final)], stdin=subprocess.PIPE)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto(f"file://{page}"); pg.wait_for_function("window.__ready===true")
        pg.evaluate("document.fonts.ready")
        last = None
        for f in range(n):
            t = f / FPS
            pg.evaluate(f"frameAt({t:.4f})")
            png = pg.screenshot(omit_background=True)
            ff.stdin.write(png)
            if f % (FPS * 5) == 0:
                print(f"  [overlay] {f}/{n}", flush=True)
        b.close()
    ff.stdin.close()
    if ff.wait():
        sys.exit("ERROR: ffmpeg overlay failed")
    run(["ffmpeg", "-y", "-v", "error", "-ss", "1.0", "-i", str(final), "-frames:v", "1", "-q:v", "3", str(out / "cover.jpg")])
    print(f"DONE {final} ({dur(final):.1f}s) main {main_dur:.1f}s + card {card_secs}s")


if __name__ == "__main__":
    main()
