# Skit run: one "Masterji ki Class" comedy short (Tue, Thu, Sat evenings)

This file is the instruction set for the skit scheduled task. Each run is a fresh Claude session;
everything it needs is in this repo. Skits are an EXTRA post: the daily explainer (DAILY_RUN.md)
still posts at 3-4 PM. Skit posts go live about 6:30-7:00 PM IST.

Channel: @bablu.masterji. Format: 25-40 s comedy with a science punchline. Read
`engine/references/skit.md` (format, sets, cast, poses, fx, sfx) and the demo
`storyboards/2026-11-18-skit-fridge-jugaad.json` before writing.

## 0. Setup
1. Attach and clone this repo with push access: `dg0975/bablu-masterji-shorts`.
2. Read `engine/SKILL.md`, `engine/references/skit.md`, and DAILY_RUN.md sections 1b (stay
   monetisable), 2b (humour), 2d (titles and engagement), 4, 4b and 5 (posting and reporting);
   those rules apply to skits too, except where this file says otherwise.

## 1. Pick the skit
- Read `topics/skits_used.csv`. **If `fridge-jugaad` is not in it, this run posts the approved
  demo `storyboards/2026-11-18-skit-fridge-jugaad.json` unchanged** (copy it to
  `storyboards/<today>-skit-fridge-jugaad.json`), then go to step 3.
- Otherwise take the first unused idea from `topics/skit_ideas.md` (or a fresher everyday idea
  with a solid science fact). Never repeat a skit or its punchline.
- Fact-check the science fact with web search; if unsure, pick another idea.

## 2. Write the skit
- 25-40 s, 5-7 shots: relatable desi moment, Golu's wrong idea or jugaad, Mummy/Papa reaction
  (belan, newspaper, facepalm), Masterji's 2 short lines explaining the science, Golu's punchline,
  ending card (`card`) with the checked fact and a one-word comment question.
- **Voices: always exactly these (the owner approved them):**
  `"cast":{"golu":{"name":"Golu","voice":"kunal_hi_kids","pace":1.4},"mummy":{"name":"Mummy","voice":"roopa_hi_conversational"},"papa":{"name":"Papa","voice":"ashok_hi_character","pace":1.5},"masterji":{"name":"Masterji"}}`
  plus `"tts":"sarvam","lead":0.15,"gap":0.2,"outro":1.4,"music_style":"funky","music":0.16,"duck":0.65`.
- Lines are short spoken Hindi in Devanagari (Golu and Papa lines up to ~10 words, they speak
  slower). Funny but family-friendly: roast situations, never groups; Mummy's belan is a joke
  prop, never actual hitting. No real people, brands or other creators' characters or songs.
- Vary sets, shot order and gags from the last 3 skits. Save `"post_title"` and `"format":"skit"`.

## 3. Voice, check, render
1. Save to `storyboards/<YYYY-MM-DD>-skit-<slug>.json`, commit and push to `main`.
2. `bash scripts/get_voice.sh storyboards/<file>.json work/voice`
3. `python3 <engine>/scripts/make_short.py storyboards/<file>.json --out work --check --tts sarvam --voice-dir work/voice --min 15 --max 40`
   View the preview sheet: faces not cut off, effects above heads, subtitles readable, no
   `PAGE ERROR`. If the total is over 40 s, shorten lines (push + get_voice again).
4. Full render the same way without `--check` (detached, as SKILL.md says).

## 4. Post and report
- Publish with `bash scripts/publish_pages.sh work/short.mp4 work/cover.jpg <date>-skit-<slug>`.
- Instagram via Windsor (`create_video_post`) and YouTube Short via Metricool exactly as
  DAILY_RUN.md steps 4 and 4b (keyword-first title, caption ending `🎙️ AI voice · Facts: <source>`,
  first-comment quiz/question, `madeForKids` false, `isAiGeneratedContent` false).
- Caption style for skits: the funny situation first ("Golu ka garmi wala jugaad 😂"), then the
  science line, the comment question, 4-5 hashtags (#comedy #scienceinhindi #hindimemes #golu + 1 topic).
- Append to `topics/skits_used.csv`: `date,slug,idea,status,instagram_media_id`; commit and push.
- Send the owner the MP4 and links (SendUserMessage + SendUserFile), short, phone-friendly.
