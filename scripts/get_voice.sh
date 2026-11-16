#!/usr/bin/env bash
# Wait for the GitHub voice job to finish for a storyboard you just pushed, then copy its clips.
# usage: scripts/get_voice.sh storyboards/<file>.json <dest-dir>
# exit 0 = clips in <dest-dir>/clips ; 2 = voice job reported an error ; 3 = timed out (8 min)
set -uo pipefail
SB=$1; DEST=$2
REPO_DIR=$(cd "$(dirname "$0")/.." && pwd)
STEM=$(basename "$SB" .json)
WANT=$(md5sum "$SB" | cut -d' ' -f1)
mkdir -p "$DEST"
for i in $(seq 1 48); do
  if git -C "$REPO_DIR" fetch -q --depth 1 origin voice 2>/dev/null; then
    ST=$(git -C "$REPO_DIR" show "FETCH_HEAD:status/$STEM.json" 2>/dev/null || true)
    if [ -n "$ST" ]; then
      GOT=$(printf '%s' "$ST" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["storyboard_md5"], d["ok"])')
      if [ "${GOT%% *}" = "$WANT" ]; then
        if [ "${GOT##* }" = "True" ]; then
          git -C "$REPO_DIR" archive FETCH_HEAD clips | tar -x -C "$DEST"
          printf '%s\n' "$ST" > "$DEST/status.json"
          echo "VOICE READY: $(ls "$DEST/clips" | wc -l) clips in $DEST/clips"
          exit 0
        fi
        echo "VOICE ERROR: $(printf '%s' "$ST" | python3 -c 'import json,sys; print(json.load(sys.stdin)["error"])')" >&2
        exit 2
      fi
    fi
  fi
  sleep 10
done
echo "VOICE TIMEOUT: no clips for $STEM after 8 minutes (is the voice workflow running?)" >&2
exit 3
