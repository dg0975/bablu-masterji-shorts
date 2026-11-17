#!/usr/bin/env python3
"""
GitHub Actions job: read public stats for the Bablu Masterji YouTube channel with the
YOUTUBE_API_KEY repo secret (read-only key; it cannot upload) and write out/stats.json,
which the workflow publishes on the `stats` branch for the daily run to read.
"""
import datetime, json, os, urllib.error, urllib.parse, urllib.request
from pathlib import Path

CHANNEL = os.environ.get("YT_CHANNEL_ID", "UCb_-_bVPgv_0mmQ0um1-DYw")
API = "https://www.googleapis.com/youtube/v3/"
KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()
OUT = Path("out"); OUT.mkdir(exist_ok=True)


def get(path, **params):
    params["key"] = KEY
    url = API + path + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            msg = json.loads(body)["error"]["message"]
        except Exception:  # noqa
            msg = body[:300]
        raise RuntimeError(f"HTTP {e.code}: {msg}".replace(KEY, "***")) from None


def main():
    res = {"ok": True, "error": None, "checked_at": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
           "channel": None, "videos": []}
    try:
        if not KEY:
            raise RuntimeError("YOUTUBE_API_KEY secret is missing in the repo settings")
        ch = get("channels", part="snippet,statistics,contentDetails", id=CHANNEL)["items"]
        if not ch:
            raise RuntimeError(f"channel {CHANNEL} not found")
        c = ch[0]; st = c["statistics"]
        res["channel"] = {"title": c["snippet"]["title"], "handle": c["snippet"].get("customUrl"),
                          "subscribers": int(st.get("subscriberCount", 0)), "views": int(st.get("viewCount", 0)),
                          "videos": int(st.get("videoCount", 0))}
        uploads = c["contentDetails"]["relatedPlaylists"]["uploads"]
        items = get("playlistItems", part="contentDetails", playlistId=uploads, maxResults=50).get("items", [])
        ids = [i["contentDetails"]["videoId"] for i in items]
        if ids:
            for v in get("videos", part="snippet,statistics", id=",".join(ids)).get("items", []):
                s = v["statistics"]
                res["videos"].append({"id": v["id"], "title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"],
                                      "views": int(s.get("viewCount", 0)), "likes": int(s.get("likeCount", 0)),
                                      "comments": int(s.get("commentCount", 0)), "url": f"https://www.youtube.com/shorts/{v['id']}"})
        res["videos"].sort(key=lambda v: v["published"], reverse=True)
        print(f"OK: {res['channel']['title']}, {res['channel']['subscribers']} subscribers, {len(res['videos'])} videos")
    except Exception as e:  # noqa
        res["ok"] = False; res["error"] = str(e)
        print("YOUTUBE ERROR:", res["error"])
    (OUT / "stats.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
