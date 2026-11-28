"""
Turn painted background images (art/src/<name>.png, from the Gemini app) into 1080x1920 skit sets
(engine/assets/bg/<name>.jpg + <name>.json layout). Settings per image live in art/bg_layout.json:
  band [y0,y1]  rows of the real picture when the app framed a wide image inside a tall one (else full)
  cx            left edge of the 1080 crop in the scaled picture; T top of the picture in the frame
  objects in source pixels (info display, windows, steam, ...) are mapped into frame coordinates.
Usage: python3 scripts/make_bg.py [name ...]
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "art" / "src", ROOT / "engine" / "assets" / "bg"
W, H = 1080, 1920


def build(name, L):
    im = Image.open(SRC / f"{name}.png").convert("RGB")
    sw, sh = im.size
    y0, y1 = L.get("band", [0, sh])
    band = im.crop((0, y0, sw, y1))
    for (x, y, w, h) in L.get("patch", []):            # hide the app's sparkle mark: copy pixels from the left
        band.paste(band.crop((x - w - 10, y - y0, x - 10, y - y0 + h)), (x, y - y0))
    s = L.get("scale") or (L.get("band_h", 1030) / (y1 - y0))
    bw, bh = round(sw * s), round((y1 - y0) * s)
    big = band.resize((bw, bh), Image.LANCZOS)
    cx, T = L.get("cx", (bw - W) // 2), L.get("T", 320)
    frame = Image.new("RGB", (W, H))
    if T > 0:   # above the picture: its top rows stretched and blurred (ceiling / sky)
        top = big.crop((cx, 0, cx + W, 60)).resize((W, T + 60)).filter(ImageFilter.GaussianBlur(24))
        frame.paste(top, (0, 0))
    frame.paste(big.crop((cx, 0, cx + W, bh)), (0, T))
    bot = T + bh
    if bot < H:  # below: the floor's last rows stretched (no reflections), soft and a little darker toward the camera
        fx0, fx1 = L.get("floor_x", [0, W])            # columns with clean floor (no objects reaching the edge)
        fl = big.crop((cx + fx0, bh - 36, cx + fx1, bh - 6)).resize((W, H - bot + 40)).filter(ImageFilter.GaussianBlur(10))
        dark = Image.new("RGB", fl.size, (20, 12, 10))
        g = Image.linear_gradient("L").resize(fl.size).point(lambda v: int(v * .32))
        fl = Image.composite(dark, fl, g)
        frame.paste(fl, (0, bot - 40), Image.linear_gradient("L").resize((W, 40)).resize(fl.size) if False else None)
        frame.paste(big.crop((cx, bh - 40, cx + W, bh)), (0, bot - 40), Image.linear_gradient("L").resize((W, 40)).transpose(Image.FLIP_TOP_BOTTOM))
    if T > 0:
        frame.paste(big.crop((cx, 0, cx + W, 40)), (0, T), Image.linear_gradient("L").resize((W, 40)))
    OUT.mkdir(parents=True, exist_ok=True)
    frame.save(OUT / f"{name}.jpg", quality=90)
    X = lambda x: round(x * s - cx); Y = lambda y: round((y - y0) * s + T)
    meta = {k: v for k, v in L.get("meta", {}).items()}
    if "info" in L:
        x, y, x2, y2 = L["info"]["box"]; meta["info"] = {"kind": L["info"]["kind"], "x": X(x), "y": Y(y), "w": X(x2) - X(x), "h": Y(y2) - Y(y)}
    if "windows" in L:
        meta["windows"] = [[X(a), Y(b), X(c) - X(a), Y(d) - Y(b)] for a, b, c, d in L["windows"]]
    if "steam" in L:
        meta["steam"] = [[X(a), Y(b)] for a, b in L["steam"]]
    (OUT / f"{name}.json").write_text(json.dumps(meta))
    print(name, "->", OUT / f"{name}.jpg", meta)


if __name__ == "__main__":
    lay = json.loads((ROOT / "art" / "bg_layout.json").read_text())
    for n in (sys.argv[1:] or lay):
        build(n, lay[n])
