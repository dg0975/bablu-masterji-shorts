#!/usr/bin/env python3
"""
Cut a front-facing character image (plain light background) into animatable parts for skit.html.

usage: make_puppet.py <image.png> <out_dir> <rig.json>
rig.json (image pixel coords of the ORIGINAL image):
 {"bg_floor_y": 655, "head_cut_y": 246, "neck": [140,230,236,264],
  "hemL": [[65,346],[110,374]], "hemR": [[258,372],[303,346]], "armL_xmax": 112, "armR_xmin": 256,
  "browL": [120,126,170,150], "browR": [197,126,247,150],
  "eyeL": [147.5,167,18,12.5], "eyeR": [220.5,167,18,12.5], "mouth": [185,205,36,11]}
(coordinates refer to the cleaned crop written as cut.png in out_dir; run with --cut-only first to get it)
Writes head.png, body.png, armL.png, armR.png, browL.png, browR.png and puppet.json.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage


def cutout_ai(path):
    """AI matting (rembg isnet-general-use); handles white clothes on a white background"""
    from rembg import remove, new_session
    im = Image.open(path).convert("RGB")
    al = np.asarray(remove(im, session=new_session("isnet-general-use"))).astype(float)[..., 3] / 255
    a = np.asarray(im).astype(float)
    edge = np.concatenate([a[:10].reshape(-1, 3), a[-10:].reshape(-1, 3)])
    bgc = np.median(edge, axis=0)
    lab, n = ndimage.label(al > .5)
    if n > 1:
        al *= ndimage.binary_dilation(lab == (np.argmax(ndimage.sum(np.ones_like(al), lab, range(1, n + 1))) + 1), iterations=3)
    ys, xs = np.where(al > .5)
    x0, x1, y0, y1 = max(0, xs.min() - 10), min(a.shape[1], xs.max() + 11), max(0, ys.min() - 8), min(a.shape[0], ys.max() + 9)
    a, al = a[y0:y1, x0:x1], al[y0:y1, x0:x1]
    A = al[..., None]
    rgb = np.clip(np.where(A > .02, (a - (1 - A) * bgc) / np.maximum(A, .02), 0), 0, 255)
    return np.dstack([rgb, al * 255]).astype(np.uint8)


def cutout(path, floor_y=None):
    try:
        return cutout_ai(path)
    except Exception as e:  # noqa  (rembg not installed: colour-key fallback)
        print("rembg unavailable, colour-key cutout:", e)
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    edge = np.concatenate([a[:10].reshape(-1, 3), a[-10:].reshape(-1, 3), a[:, :10].reshape(-1, 3), a[:, -10:].reshape(-1, 3)])
    bgc = np.median(edge, axis=0)
    d = np.sqrt(((a - bgc) ** 2).sum(2))
    lab, n = ndimage.label(d < 12)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    fg = ndimage.binary_fill_holes(~np.isin(lab, list(border)))
    band = ndimage.binary_dilation(fg, iterations=2) & ~ndimage.binary_erosion(fg, iterations=1)
    al = fg.astype(float)
    al[band] = np.clip((d[band] - 4) / 22, 0, 1)
    al = ndimage.gaussian_filter(al, .6) * np.maximum(fg, band)
    ys, xs = np.where(al > .5)
    x0, x1, y0, y1 = max(0, xs.min() - 10), min(a.shape[1], xs.max() + 11), max(0, ys.min() - 8), min(a.shape[0], ys.max() + 9)
    a, al, d = a[y0:y1, x0:x1], al[y0:y1, x0:x1], d[y0:y1, x0:x1]
    A = al[..., None]
    rgb = np.clip(np.where(A > .02, (a - (1 - A) * bgc) / np.maximum(A, .02), 0), 0, 255)
    lum, sat = rgb.mean(2), rgb.max(2) - rgb.min(2)
    H = a.shape[0]
    fy = floor_y if floor_y else int(H * .905)
    yy = np.arange(H)[:, None] * np.ones((1, a.shape[1]))
    al[(yy > fy) & (lum > 150) & (sat < 30)] = 0                   # soft floor shadow
    low = yy > H * .58
    al[low & (d < 16)] = 0                                         # background trapped between the legs
    part = low & (d >= 16) & (d < 30) & (al > 0)
    al[part] *= (d[part] - 16) / 14
    lab, n = ndimage.label(al > .3)
    if n > 1:
        sizes = ndimage.sum(np.ones_like(al), lab, range(1, n + 1))
        al *= ndimage.binary_dilation(lab == (np.argmax(sizes) + 1), iterations=2)
    al[(al > 0) & (al < 1) & (lum > 200)] *= .35                   # light fringe
    return np.dstack([rgb, al * 255]).astype(np.uint8)


def lab(rgb):
    import cv2
    return cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(float)


def auto_arms(c, R):
    """find bare arms by the face's skin colour; returns {side: mask}. Bangles, watches and finger gaps are
    closed vertically so the whole forearm comes out in one piece."""
    rgb, al = c[..., :3], c[..., 3]
    H, W = al.shape
    L = lab(rgb)
    mx, my, mrx, mry = R["mouth"]
    ref = np.median(L[int(my) - 2:int(my) + 3, int(mx - mrx - 10):int(mx - mrx - 4)].reshape(-1, 3), axis=0)
    d = np.sqrt(((L[..., 0] - ref[0]) * .35) ** 2 + (L[..., 1] - ref[1]) ** 2 + (L[..., 2] - ref[2]) ** 2)
    skin = (d < R.get("arm_tol", 16)) & (al > 128)
    yy, xx = np.mgrid[0:H, 0:W]
    cx = R.get("center_x", W / 2)
    y_lo, y_hi = R.get("arm_y", [int(H * .3), int(H * .82)])
    out = {}
    for side, cond in (("L", xx < cx - W * .08), ("R", xx > cx + W * .08)):
        if R.get("arm" + side) is False:
            continue
        m = skin & cond & (yy > y_lo) & (yy < y_hi)
        lab_, n = ndimage.label(m)
        if n == 0:
            continue
        sizes = ndimage.sum(m, lab_, range(1, n + 1))
        k = int(np.argmax(sizes)) + 1
        if sizes[k - 1] < 300:
            continue
        m = lab_ == k
        m = ndimage.binary_closing(m, structure=np.ones((23, 3)), iterations=1)
        m = ndimage.binary_fill_holes(m) & (al > 20)
        m = ndimage.binary_dilation(m, iterations=1) & (al > 20) & cond & (yy > y_lo)
        out[side] = m
    return out


def fill_behind(c, m, side):
    """remove an arm from the body: inpaint cloth where the torso continues behind it, clear the rest"""
    import cv2
    rgb, al = c[..., :3].copy(), c[..., 3].copy()
    H, W = al.shape
    keep = np.zeros_like(m)
    for y in range(H):
        xs = np.where(m[y])[0]
        if len(xs) == 0:
            continue
        x0, x1 = xs.min(), xs.max()
        inner = x1 + 2 if side == "L" else x0 - 2          # the torso side of the arm
        if 0 <= inner < W and al[y, inner] > 200 and not m[y, inner]:
            mid = (x0 + x1) / 2
            if side == "L":
                keep[y, int(mid):x1 + 1] = True
            else:
                keep[y, x0:int(mid) + 1] = True
    keep &= m
    hole = (m.astype(np.uint8) * 255)
    src = rgb.astype(np.uint8).copy()
    src[m] = 0
    filled = cv2.inpaint(src, hole, 7, cv2.INPAINT_TELEA)
    c2 = c.copy()
    c2[..., :3] = np.where(keep[..., None], filled, c[..., :3])
    a = al.copy(); a[m & ~keep] = 0
    c2[..., 3] = a
    return c2


def save(arr, path):
    Image.fromarray(arr.astype(np.uint8), "RGBA").save(path, optimize=True)


def crop_box(arr):
    ys, xs = np.where(arr[..., 3] > 8)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def main():
    src, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    if sys.argv[3:4] == ["--cut-only"]:
        save(cutout(src), out / "cut.png"); print("wrote", out / "cut.png"); return
    R = json.loads(Path(sys.argv[3]).read_text())
    c = cutout(src, R.get("bg_floor_y")).astype(float)
    save(c, out / "cut.png")
    H, W = c.shape[:2]
    rgb, al = c[..., :3], c[..., 3]
    yy, xx = np.mgrid[0:H, 0:W]
    skin = (rgb[..., 0] > 105) & (rgb[..., 0] > rgb[..., 2] + 22) & (al > 20)
    parts, meta = {}, {"w": W, "h": H}

    def below(hem, x, y):
        (xa, ya), (xb, yb) = hem
        return y > ya + (np.clip(x, min(xa, xb), max(xa, xb)) - xa) * (yb - ya) / (xb - xa) + 1

    body = c.copy()
    from PIL import ImageDraw
    poly_masks = {}
    for side in ("L", "R"):
        if R.get("arm" + side + "_poly"):
            pm = Image.new("L", (W, H), 0)
            ImageDraw.Draw(pm).polygon([tuple(q) for q in R["arm" + side + "_poly"]], fill=255)
            m = (np.asarray(pm) > 0) & (al > 20)
            m = ndimage.binary_dilation(m, iterations=3) & (al > 20)
            poly_masks[side] = m
    arm_sets = auto_arms(c, R).items() if R.get("arms") == "auto" else poly_masks.items()
    if arm_sets:
        for side, m in arm_sets:
            arm = np.zeros_like(c); arm[m] = c[m]
            ys, xs = np.where(m)
            top = ys.min()
            tx = xs[ys < top + 6]
            if not poly_masks:            # arms behind the body: grow the top under the sleeve
                for y in range(top - 1, max(0, top - 14), -1):
                    arm[y] = np.where(arm[y + 1, :, 3:4] > 0, arm[y + 1], arm[y])
            parts["arm" + side] = arm
            pl = R.get("arm" + side + "_poly")
            pv = [(pl[0][0] + pl[1][0]) / 2, (pl[0][1] + pl[1][1]) / 2 + 4] if pl else [float(tx.mean()), float(top + 4)]
            meta["arm" + side] = {"pivot": pv}
            body = fill_behind(body, m, side)
        if poly_masks:
            meta["armsFront"] = True          # traced arms lie over the body, so they draw in front of it
        if R.get("armRange"):
            meta["armRange"] = R["armRange"]
    arms = [] if "hemL" not in R else [("L", R["hemL"], xx <= R["armL_xmax"]), ("R", R["hemR"], xx >= R["armR_xmin"])]
    for side, hem, cond in arms:
        m = skin & cond & below(hem, xx, yy)
        lab, n = ndimage.label(m)
        m = lab == (np.argmax(ndimage.sum(m, lab, range(1, n + 1))) + 1)
        m = ndimage.binary_dilation(m, iterations=1) & (al > 0) & cond & below(hem, xx, yy)
        arm = np.zeros_like(c); arm[m] = c[m]
        body[ndimage.binary_dilation(m, iterations=3) & cond & below(hem, xx, yy) & ~(skin & ~m)] = 0
        # extend the arm's top under the sleeve so rotating never shows a gap
        top = min(hem[0][1], hem[1][1])
        for y in range(int(max(hem[0][1], hem[1][1])) + 3, int(top) - 16, -1):
            row = arm[y]
            if (row[:, 3] > 0).sum() < 4 and y + 1 < H:
                src_row = arm[y + 1].copy()
                arm[y] = np.where((src_row[:, 3:4] > 0) & (np.arange(W)[:, None] >= 0), src_row, row)
        parts["arm" + side] = arm
        pv = [(hem[0][0] + hem[1][0]) / 2, (hem[0][1] + hem[1][1]) / 2]
        meta["arm" + side] = {"pivot": pv}
    # head (with neck) drawn behind the body; the body loses its neck skin so the head's neck shows
    nx0, nx1, ny0, ny1 = R["neck"]
    neckzone = (xx >= nx0) & (xx <= nx1) & (yy >= ny0) & (yy <= ny1)
    head_m = (al > 0) & ((yy < R["head_cut_y"]) | (neckzone & skin))
    head = np.zeros_like(c); head[head_m] = c[head_m]
    # neck extends a bit lower under the collar
    for y in range(ny1 + 1, min(H, ny1 + 10)):
        head[y, nx0 + 8:nx1 - 8] = np.where(head[y - 1, nx0 + 8:nx1 - 8, 3:4] > 0, head[y - 1, nx0 + 8:nx1 - 8], head[y, nx0 + 8:nx1 - 8])
    body[(yy < R["head_cut_y"]) | (neckzone & skin)] = 0
    # brows: cut out, inpaint the forehead
    import cv2
    hb = head[..., :3].astype(np.uint8).copy()
    holes = np.zeros((H, W), np.uint8)
    for side in (("L", "R") if R.get("browL") else ()):
        x0, y0, x1, y1 = R["brow" + side]
        box = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)
        m = box & (rgb.mean(2) < R.get("brow_thr", 95)) & (al > 0)
        lab, n = ndimage.label(m)
        if n > 1:
            m = lab == (np.argmax(ndimage.sum(m, lab, range(1, n + 1))) + 1)
        m = ndimage.binary_dilation(m, iterations=1) & box
        b = np.zeros_like(c); b[m] = c[m]
        parts["brow" + side] = b
        holes |= ndimage.binary_dilation(m, iterations=1).astype(np.uint8)
        meta["brow" + side] = {"center": [(x0 + x1) / 2, (y0 + y1) / 2]}
    hb = cv2.inpaint(hb, holes * 255, 9, cv2.INPAINT_NS)
    head[..., :3] = np.where(holes[..., None] > 0, hb, head[..., :3])
    if R.get("stache"):
        x0, y0, x1, y1 = R["stache"]
        box = (xx >= x0) & (xx <= x1) & (yy >= y0) & (yy <= y1)
        m = box & (rgb.mean(2) < R.get("stache_thr", 110)) & (al > 0)
        lab, n = ndimage.label(m)
        if n > 1:
            m = lab == (np.argmax(ndimage.sum(m, lab, range(1, n + 1))) + 1)
        m = ndimage.binary_closing(m, iterations=2) & box
        st = np.zeros_like(c); st[m] = c[m]
        st[..., 3] = (ndimage.gaussian_filter(m.astype(float), .7) * al).clip(0, 255)
        parts["stache"] = st
    parts["head"], parts["body"] = head, body
    meta["headPivot"] = [(nx0 + nx1) / 2, ny0 + 8]
    # colours for lids / mouth patch, sampled from the skin
    def samp(x, y, r=3):
        p = c[int(y) - r:int(y) + r, int(x) - r:int(x) + r, :3].reshape(-1, 3)
        return "#%02x%02x%02x" % tuple(int(v) for v in np.median(p, axis=0))
    ex, ey, erx, ery = R["eyeL"]
    fx, fy = (R["eyeL"][0] + R["eyeR"][0]) / 2, ey                  # between the eyes: clean, evenly lit skin
    meta["eyeL"], meta["eyeR"], meta["mouth"] = R["eyeL"], R["eyeR"], R["mouth"]
    meta["lid"] = samp(*R["lid_at"]) if R.get("lid_at") else samp(fx, fy)
    meta["cheek"] = samp(ex, ey + ery + 8)
    mx, my, mrx, mry = R["mouth"]
    meta["skinMouth"] = [samp(mx - mrx - 6, my), samp(mx, my + mry + 10), samp(mx + mrx + 6, my)]
    for k, v in parts.items():
        x0, y0, x1, y1 = crop_box(v)
        save(v[y0:y1, x0:x1], out / f"{k}.png")
        meta.setdefault(k, {})["at"] = [x0, y0, x1 - x0, y1 - y0]
    (out / "puppet.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
