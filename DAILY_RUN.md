# Daily run: one Bablu Masterji short, made and posted

This file is the instruction set for the daily scheduled task. Each run is a fresh Claude
session with no memory of earlier runs; everything it needs is in this repo.

Channel: **@bablu.masterji** (Instagram Reels via Windsor.ai; YouTube Shorts via Metricool).
Language: Hindi narration, Hinglish on-screen text. Mascot: Bablu Masterji.

**Test runs:** if the task prompt says TEST RUN, do everything except steps 4 and 4b (no
gh-pages push, no Instagram or YouTube post), log nothing, and send the user the video and
post text.

## 0. Setup

1. Attach and clone this repo with push access: `dg0975/bablu-masterji-shorts`.
2. Read `engine/SKILL.md` fully, then `engine/references/storyboard.md` and
   `engine/examples/pressure_cooker.json`. Follow SKILL.md for the video; this file adds the
   topic choice, quality gates, posting and logging. Work from a copy of `engine/` in the
   working directory, not inside the repo checkout.
3. Voice: the channel voice is **Sarvam AI, speaker `girish_hi_devotional`** (model
   `bulbul:v4-flash`). The API key lives only in the repo's GitHub secret, so the clips are made
   by the GitHub workflow `.github/workflows/voice.yml` whenever a storyboard is pushed, and
   published on the `voice` branch. Never ask for or handle the key yourself.
   Backup voice, only if Sarvam fails: Microsoft `hi-IN-MadhurNeural` through edge-tts, which
   needs `speech.platform.bing.com`. Never make or post a silent video.

## 1. Pick today's topic

- Read `topics/used.csv`. Never repeat a topic or a near-duplicate of one already used.
- Take the first unused line of `topics/ideas.md`, or, if a fresher everyday-science question
  fits the season or news better, use that instead. Public, general-knowledge topics only.
- No health or medical advice, no diet or "cure" topics, nothing political or religious,
  no real people or brands.
- Fact-check the explanation and every number with web search before writing. If the sources
  disagree or you cannot confirm a key number, pick another topic.

## 2. Make the video

Follow `engine/SKILL.md` steps 1-4 (storyboard, `--check`, fix, full render), with the voice
made like this:

1. Save the storyboard to `storyboards/<YYYY-MM-DD>-<slug>.json` with
   `"handle": "@bablu.masterji"` and `"tts": "sarvam"`. Commit and push it to `main`
   (message `storyboard: <date> <slug>`).
2. `bash scripts/get_voice.sh storyboards/<file>.json work/voice` waits (up to 8 min) for the
   GitHub voice job and copies the clips.
3. `python3 <engine>/scripts/make_short.py storyboards/<file>.json --out work --check --tts sarvam --voice-dir work/voice`
   then the full render the same way (detached, as SKILL.md says).
4. Every time you change any `say` text, commit and push the storyboard again and rerun
   `get_voice.sh` before rendering; changed lines get new clips, unchanged ones are reused.
5. If `get_voice.sh` exits with `VOICE ERROR` or `VOICE TIMEOUT`, use the backup voice:
   render with `--tts edge` (Microsoft Madhur) and mention it in the report. If edge is not
   reachable either, stop: no video today, and tell the user why.

Sarvam reads numbers well, but still spell key numbers as words in `say` for consistency.

## 3. Quality gates (all must pass to post automatically)

- Total length 50-68 s; no `LAYOUT:` or `PAGE ERROR:` lines left after fixes.
- You viewed the preview sheet and it looks right (no clipped text, visual not empty).
- Every stated number was confirmed by a source; rounded ones say लगभग and carry a tag.
- The final MP4 exists, is 1080x1920, has an audio stream (check with ffprobe).
- The voice engine was `sarvam` (or `edge` as backup). If it fell back to `gtts` (Google basic
  voice, very robotic), do not post: hold it and tell the user.

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

## 4b. Post to YouTube Shorts (Metricool)

Only if the quality gates passed. Uses the same PUBLIC_URL as step 4.

1. Metricool `getBrandSettings`: brand id `8158859`, timezone `Asia/Calcutta`, and
   `networksData.youtubeData` must be set. If YouTube is not connected, skip this step and
   tell the user to reconnect it at https://app.metricool.com/brands/connections?blogId=8158859
2. `createScheduledPost` with `blogId` 8158859, `date` = now + 6 minutes (IST, ISO 8601 with
   +05:30), and `info`:
   - `providers` `[{"network":"youtube"}]`, `media` `[PUBLIC_URL]`, `autoPublish` true
   - `text` = the YouTube description (2-3 Hinglish lines + 8-10 hashtags starting `#shorts`)
   - `youtubeData`: `title` under 60 characters ending in `#shorts`, `type` `short`,
     `privacy` `public`, `category` `EDUCATION`, `madeForKids` **false** (user's choice),
     `isAiGeneratedContent` false (animated cartoon, not realistic), 5-8 `tags`
   - `publicationDate` `{dateTime, timezone: "Asia/Calcutta"}` matching `date`
3. Wait about 7 minutes, then `getScheduledPosts` for today: the YouTube provider should show
   `status` `PUBLISHED` with a `publicUrl`. If it shows an error, do not retry more than once;
   tell the user.

## 5. Log and report

1. Append to `topics/used.csv`: `date,slug,topic,status,instagram_media_id,youtube_url`
   (status `posted`, `held` or `post_failed`; leave a field empty if that platform failed). Commit the storyboard and the log to `main`
   with message `short: <date> <slug>` and push.
2. Send the user (SendUserMessage + SendUserFile) the MP4 and cover, with:
   - whether it went live on Instagram and YouTube (with the YouTube Shorts link),
   - any approximate number to double-check, and a note that you cannot hear the audio.

Keep the report short: the user reads it on a phone.
