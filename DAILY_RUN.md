# Daily run: one Bablu Masterji short, made and posted

This file is the instruction set for the daily scheduled task. Each run is a fresh Claude
session with no memory of earlier runs; everything it needs is in this repo.

Channel: **@bablu.masterji** (Instagram Reels; YouTube Shorts posted by hand for now).
Language: Hindi narration, Hinglish on-screen text. Mascot: Bablu Masterji.

**Test runs:** if the task prompt says TEST RUN, do everything except step 4 (no gh-pages
push, no Instagram post), log nothing, and send the user the video and post text.

## 0. Setup

1. Attach and clone this repo with push access: `dg0975/bablu-masterji-shorts`.
2. Read `engine/SKILL.md` fully, then `engine/references/storyboard.md` and
   `engine/examples/pressure_cooker.json`. Follow SKILL.md for the video; this file adds the
   topic choice, quality gates, posting and logging. Work from a copy of `engine/` in the
   working directory, not inside the repo checkout.
3. Network check: the voice needs `speech.platform.bing.com` (or `translate.google.com`).
   If neither is reachable, stop here and send the user a message saying the voice domains
   are blocked. Never make or post a silent video.

## 1. Pick today's topic

- Read `topics/used.csv`. Never repeat a topic or a near-duplicate of one already used.
- Take the first unused line of `topics/ideas.md`, or, if a fresher everyday-science question
  fits the season or news better, use that instead. Public, general-knowledge topics only.
- No health or medical advice, no diet or "cure" topics, nothing political or religious,
  no real people or brands.
- Fact-check the explanation and every number with web search before writing. If the sources
  disagree or you cannot confirm a key number, pick another topic.

## 2. Make the video

Follow `engine/SKILL.md` steps 1-4 (storyboard, `--check`, fix, full render).
Save the storyboard to `storyboards/<YYYY-MM-DD>-<slug>.json` in the repo.
`"handle": "@bablu.masterji"` in every storyboard.

## 3. Quality gates (all must pass to post automatically)

- Total length 50-68 s; no `LAYOUT:` or `PAGE ERROR:` lines left after fixes.
- You viewed the preview sheet and it looks right (no clipped text, visual not empty).
- Every stated number was confirmed by a source; rounded ones say लगभग and carry a tag.
- The final MP4 exists, is 1080x1920, has an audio stream (check with ffprobe).

If any gate fails: do not post. Log the topic with status `held` and send the user the
video (if any) plus one line saying which gate failed.

## 4. Post to Instagram (Windsor.ai for Social Media)

1. `bash scripts/publish_pages.sh work/short.mp4 work/cover.jpg <YYYY-MM-DD>-<slug>`
   prints `PUBLIC_URL` once the video is live on GitHub Pages.
2. Windsor tools: `get_connectors` (connector `instagram`, account `bablu.masterji`), then
   `execute_action` with action `create_video_post`, params:
   `video_url` = PUBLIC_URL, `caption` = Hinglish caption (2-3 lines) + call to comment
   "Present" + 8-10 hashtags, `share_to_feed` = true,
   `thumb_offset` = milliseconds of the hook frame (first beat's audio end from
   `work/timeline.json`, times 1000).
3. If the script printed `UNVERIFIED` and Windsor says the video URL could not be fetched,
   wait 3 minutes and call it once more. For any other Windsor error (expired trial,
   disconnected account, rejected video), do not retry more than once. Log status `post_failed` and send the user the video and the error.

## 5. Log and report

1. Append to `topics/used.csv`: `date,slug,topic,status,instagram_media_id`
   (status `posted`, `held` or `post_failed`). Commit the storyboard and the log to `main`
   with message `short: <date> <slug>` and push.
2. Send the user (SendUserMessage + SendUserFile) the MP4 and cover, with:
   - whether it went live on Instagram,
   - ready-to-paste **YouTube Short** text: title under 60 characters ending in `#shorts`,
     a 2-3 line description, and 8-10 hashtags,
   - any approximate number to double-check, and a note that you cannot hear the audio.

Keep the report short: the user reads it on a phone.
