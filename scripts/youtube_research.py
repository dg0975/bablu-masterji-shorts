#!/usr/bin/env python3
"""
GitHub Actions job: read PUBLIC data (titles, views, likes, comments, length) of another channel's
latest uploads, for format research only (what kinds of situations work), never to copy content.
Handle comes from research-request.txt; output out/research-<handle>.json on the `research` branch.
"""
import json, os, re, urllib.parse, urllib.request, urllib.error
from pathlib import Path

KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
API = "https://www.googleapis.com/youtube/v3/"
OUT = Path("out"); OUT.mkdir(exist_ok=True)


def get(path, **p):
    p["key"] = KEY
    try:
        with urllib.request.urlopen(API + path + "?" + urllib.parse.urlencode(p), timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode(errors='replace')[:300]}".replace(KEY, "***")) from None


def secs(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    return sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else 0


handle = (Path("research-request.txt").read_text().split() or ["@wagguy"])[0].strip()
res = {"handle": handle, "ok": True, "error": None, "channel": None, "videos": []}
try:
    ch = get("channels", part="snippet,statistics,contentDetails", forHandle=handle).get("items", [])
    if not ch:
        raise RuntimeError("channel not found")
    c = ch[0]
    res["channel"] = {"title": c["snippet"]["title"], "subscribers": int(c["statistics"].get("subscriberCount", 0)),
                      "views": int(c["statistics"].get("viewCount", 0)), "videos": int(c["statistics"].get("videoCount", 0))}
    up = c["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while len(ids) < 100:
        r = get("playlistItems", part="contentDetails", playlistId=up, maxResults=50, **({"pageToken": tok} if tok else {}))
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        tok = r.get("nextPageToken")
        if not tok:
            break
    for k in range(0, len(ids), 50):
        for v in get("videos", part="snippet,statistics,contentDetails", id=",".join(ids[k:k + 50])).get("items", []):
            s = v["statistics"]
            res["videos"].append({"title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"][:10],
                                  "secs": secs(v["contentDetails"]["duration"]), "views": int(s.get("viewCount", 0)),
                                  "likes": int(s.get("likeCount", 0)), "comments": int(s.get("commentCount", 0)),
                                  "tags": v["snippet"].get("tags", [])[:8], "desc": v["snippet"].get("description", "")[:160]})
    print(f"OK {res['channel']['title']}: {len(res['videos'])} videos")
except Exception as e:  # noqa
    res["ok"] = False; res["error"] = str(e); print("ERROR", e)
(OUT / f"research-{handle.lstrip('@')}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
