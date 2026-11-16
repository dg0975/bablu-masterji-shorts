#!/usr/bin/env python3
"""
GitHub Actions job: make the Sarvam voice clips for the newest storyboard.

Runs on every push that touches storyboards/*.json (see .github/workflows/voice.yml).
Writes clips/<key>.wav and status/<storyboard-stem>.json into ./voiceout, reusing clips
from the previous voice branch when the line did not change. The workflow then replaces
the `voice` branch with ./voiceout. SARVAM_API_KEY comes from the repo secret and is never printed.
"""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine" / "scripts"))
import sarvam_tts as st  # noqa: E402

OUT = ROOT / "voiceout"
PREV = ROOT / "voiceprev"     # previous voice branch, if the workflow checked it out


def newest_storyboard():
    names = subprocess.run(["git", "log", "-1", "--format=", "--name-only", "--diff-filter=AM", "--", "storyboards/"],
                           cwd=ROOT, capture_output=True, text=True).stdout.split()
    names = [n for n in names if n.endswith(".json")]
    if names:
        return ROOT / names[0]
    files = sorted((ROOT / "storyboards").glob("*.json"))
    return files[-1] if files else None


def main():
    sb_path = newest_storyboard()
    if not sb_path:
        print("no storyboard found"); return
    raw = sb_path.read_bytes()
    sb = json.loads(raw)
    cfg = st.settings(sb)
    (OUT / "clips").mkdir(parents=True, exist_ok=True)
    (OUT / "status").mkdir(parents=True, exist_ok=True)
    status = {"storyboard": str(sb_path.relative_to(ROOT)), "storyboard_md5": hashlib.md5(raw).hexdigest(),
              "engine": "sarvam", **cfg, "ok": True, "error": None, "clips": {}}
    key = os.environ.get("SARVAM_API_KEY", "").strip()
    try:
        if not key:
            raise RuntimeError("SARVAM_API_KEY secret is missing in the repo settings")
        made = reused = 0
        for i, j, text in st.lines(sb):
            k = st.clip_key(cfg, text)
            dst = OUT / "clips" / f"{k}.wav"
            old = PREV / "clips" / f"{k}.wav"
            if old.exists():
                shutil.copy(old, dst); reused += 1
            elif not dst.exists():
                st.synth(text, cfg, key, dst); made += 1
            status["clips"][k] = f"clips/{k}.wav"
        print(f"{sb_path.name}: {made} new clips, {reused} reused, speaker {cfg['speaker']}")
    except Exception as e:  # noqa
        status["ok"] = False
        status["error"] = str(e).replace(key, "***") if key else str(e)
        print("VOICE ERROR:", status["error"])
    (OUT / "status" / f"{sb_path.stem}.json").write_text(json.dumps(status, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
