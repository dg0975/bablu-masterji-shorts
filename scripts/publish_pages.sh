#!/usr/bin/env bash
# Put today's video and cover on GitHub Pages so Instagram (via Windsor.ai) can fetch them.
# usage: scripts/publish_pages.sh path/to/video.mp4 path/to/cover.jpg <slug>
# The gh-pages branch is replaced with a single fresh commit each day, so old videos
# do not pile up in the repo. Prints PUBLIC_URL and COVER_URL once the file is live.
set -euo pipefail
VID=$1; COVER=$2; SLUG=$3
REPO_DIR=$(cd "$(dirname "$0")/.." && pwd)
REMOTE=$(git -C "$REPO_DIR" remote get-url origin)
OWNER_REPO=$(echo "$REMOTE" | sed -E 's#.*github.com[:/]##; s#\.git$##')
OWNER=${OWNER_REPO%%/*}; NAME=${OWNER_REPO##*/}
BASE="https://${OWNER,,}.github.io/${NAME}"

TMP=$(mktemp -d)
cp "$VID" "$TMP/$SLUG.mp4"
cp "$COVER" "$TMP/$SLUG.jpg"
touch "$TMP/.nojekyll"
printf '<!doctype html><meta charset="utf-8"><title>Bablu Masterji</title><p>Latest short: <a href="%s.mp4">%s</a></p>\n' "$SLUG" "$SLUG" > "$TMP/index.html"
cd "$TMP"
git init -q -b gh-pages
git add -A
git -c user.name="Bablu Masterji bot" -c user.email="bot@users.noreply.github.com" commit -q -m "video $SLUG"
git push -q -f "$REMOTE" gh-pages

SHA=$(git rev-parse HEAD)
URL="$BASE/$SLUG.mp4"
SIZE=$(stat -c %s "$VID")

# make sure Pages serves the gh-pages branch (no-op if already enabled)
if [ "$(gh api "repos/$OWNER_REPO" --jq .has_pages 2>/dev/null)" != "true" ]; then
  gh api -X POST "repos/$OWNER_REPO/pages" -f 'source[branch]=gh-pages' -f 'source[path]=/' >/dev/null 2>&1 || true
fi

for i in $(seq 1 40); do
  # 1) direct check, when github.io is reachable from this sandbox
  got=$(curl -sI --max-time 20 "$URL" 2>/dev/null | awk 'tolower($1)=="content-length:"{print $2}' | tr -d '\r' || true)
  if [ "$got" = "$SIZE" ]; then
    echo "PUBLIC_URL $URL"; echo "COVER_URL $BASE/$SLUG.jpg"; exit 0
  fi
  # 2) otherwise ask the GitHub API whether this commit has been built
  st=$(gh api "repos/$OWNER_REPO/pages/builds/latest" --jq '.status + " " + .commit' 2>/dev/null || true)
  if [ "$st" = "built $SHA" ]; then
    sleep 30   # let the CDN pick it up
    echo "PUBLIC_URL $URL"; echo "COVER_URL $BASE/$SLUG.jpg"; exit 0
  fi
  sleep 15
done
echo "ERROR: $URL was not live after 10 minutes (is GitHub Pages enabled for the gh-pages branch?)" >&2
exit 1
