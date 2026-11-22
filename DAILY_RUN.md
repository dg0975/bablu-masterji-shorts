# Daily run: one Bablu Masterji short, made and posted

> **Paused since 21 Nov 2026:** the owner now posts only the evening skit (`SKIT_RUN.md`). The
> explainer scheduled task is turned off. Keep this file: SKIT_RUN.md uses its posting (4, 4b),
> monetisation (1b) and report (5) rules. Make an explainer only when the owner asks in chat.

This file is the instruction set for the daily scheduled task. Each run is a fresh Claude
session with no memory of earlier runs; everything it needs is in this repo.

Channel: **@bablu.masterji** (Instagram Reels via Windsor.ai; YouTube Shorts via Metricool).
Language: Hindi narration, Hinglish on-screen text. Mascot: Bablu Masterji.

**Test runs:** if the task prompt says TEST RUN, do everything except steps 4 and 4b (no
gh-pages push, no Instagram or YouTube post), log nothing, and send the user the video and
post text.

**Posting time:** the run starts at 14:41 IST so both posts go live between 3:00 and 4:00 PM IST
(the user's chosen slot). If a run finishes late, still post; never hold a finished video for
the next day.

## 0. Setup

1. Attach and clone this repo with push access: `dg0975/bablu-masterji-shorts`.
2. Read `engine/SKILL.md` fully, then `engine/references/storyboard.md`,
   `engine/examples/pressure_cooker.json` and `engine/examples/sky_living.json` (the living-scene
   style: animated sky, sun, clouds, light flow). Follow SKILL.md for the video; this file adds the
   topic choice, quality gates, posting and logging. Work from a copy of `engine/` in the
   working directory, not inside the repo checkout.
3. Voice: the channel voice is **Sarvam AI, speaker `harpreet_pa_narration` (Harpreet), pace
   `0.97`** (model `bulbul:v4-flash`); the user chose it on 2026-11-17 (previously Girish
   `girish_hi_devotional` at 1.05). Pace 0.97 keeps Harpreet at the same speaking speed as the
   earlier videos; do not change it. The API key lives only in the repo's GitHub secret, so the clips are made
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

## 1b. Stay monetisable: original, varied, honest (YouTube "inauthentic content", Meta rules)

YouTube demonetises channels whose videos differ only superficially (same template, same
narration pattern); Instagram expects original content. Every video must be clearly its own work:
- **Rotate the format.** Pick a format different from the last 2 storyboards (read their
  `"format"` field) and save yours as `"format"`:
  `aisa-kyun` (hook, myth, mechanism, payoff, takeaway) · `myth-vs-sach` (bust 2-3 myths in a row)
  · `kya-hoga-agar` (a "what if" scenario explained step by step) · `ghar-ka-experiment` (a safe
  experiment with everyday kitchen items, explained; nothing hot, sharp, electrical or chemical
  beyond vinegar/salt/baking soda) · `quiz-challenge` (question first, 3 clues, reveal) ·
  `3-facts` (countdown of 3 surprising facts on one theme).
- **Vary the shape:** 5-7 scenes, a different opening visual type and colour order from
  yesterday, a different Masterji opener and catchphrase.
- **No recycled lines:** do not reuse any narration sentence (or near-copy) from the last 14
  storyboards, apart from the short sign-off. Every video has at least one fresh everyday Indian
  example or analogy specific to its topic.
- **Real value:** each video must teach one clear, checked idea a viewer did not know; no padding.
- **Be transparent about AI:** the Instagram caption and YouTube description end with
  `🎙️ AI voice · Facts: <short source name>` (e.g. "Facts: NASA"). YouTube `isAiGeneratedContent`
  stays false (animated explainer, not realistic footage of real people or events).
- **Never:** health or medical advice, political or religious topics, dangerous stunts, real
  people or brand logos, other creators' clips, copied music or images, misleading titles or
  thumbnails, more than one post per day, re-uploading an old video, more than 5 hashtags.
- **Audience:** general audience (students and adults), so YouTube `madeForKids` stays false;
  do not write in nursery or kids-only style.

## 2. Make the video

Follow `engine/SKILL.md` steps 1-4 (storyboard, `--check`, fix, full render), with the voice
made like this:

1. Save the storyboard to `storyboards/<YYYY-MM-DD>-<slug>.json` with
   `"handle": "@bablu.masterji"`, `"tts": "sarvam"`,
   `"sarvam_speaker": "harpreet_pa_narration"` and `"sarvam_pace": 0.97`. Commit and push it to `main`
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

## 2b. Make it funny (engagement)

Every video needs real comedy, not only facts. Bablu Masterji is a lovable, slightly dramatic
sarkari-school teacher; the jokes come from his character and from everyday Indian life.
- **Hook joke (first 3 seconds):** open with a funny relatable line, e.g. a mummy/pressure-cooker,
  chai, Indian-traffic, power-cut, exam-fear or back-bencher situation, then the question.
- **2-3 funny lines spread through the script**, at least one in the narration (`say`) and the
  rest in bubbles/friend lines. Kinds that work: Masterji's over-the-top teacher drama
  ("Silence! Ye physics hai, koi WhatsApp forward nahi!"), a back-bencher's wrong answer that he
  roasts gently, a desi exaggeration, a self-own about his three hairs / taped glasses / chai.
- **Comment bait at the end:** a funny question or challenge viewers want to answer
  ("Comment mein batao, aapke ghar mein cooker ki kitni seeti lagti hai?") plus the
  "Present lagao" attendance gag.
- The joke must never change or blur the fact; the science stays correct and clear.
- Clean, family-friendly humour only: no insults about caste, religion, region, gender, body
  or real people; roast the situation, not a group. Do not reuse a joke used in the last
  7 storyboards (check `storyboards/`).
- Pose the mascot for the joke: `shock` for drama, `happy` after the punchline, `think` for the
  back-bencher's wrong answer.

## 2c. Make it move (realistic, living scenes)

The engine adds camera motion, background life, lip-sync and gestures by itself. The storyboard
must add the rest (details: "Living scenes" in `engine/references/storyboard.md`):
- The **hook** and the **mechanism** scene (and ideally the payoff) are custom SVG scenes that
  look like the real thing, drawn with gradients: sky, sun, cloud, kitchen, cooker, road, water.
- Every custom SVG has at least 3 continuously moving parts (`spin`, `drift`, `flow`, `orbit`,
  `bob`, `breathe`, `twinkle`, `rise`) and something new on each beat (`data-step`, `data-move`,
  `data-hide`, a cross-fade).
- Show processes as motion: light/heat/sound/air as `flow` dashes, a sun setting with
  `data-move`, a sky turning orange with a slow `fade` of a second gradient.
- Look at the preview sheet for a busy or muddy frame; motion must never cover the text.

## 2e. 3D scene: only when it shows today's concept

A 3D scene must show **the actual thing the narration is talking about at that moment**. If a
viewer muted the video, the 3D picture alone should hint at the topic. Decoration is not allowed.
- Pick the scene where depth genuinely helps (the mechanism, usually), then ask: "Is this object
  or process literally in today's topic?" Only then use 3D.
- Preset fit, by topic: `earth` = sky colour, sunsets, day/night, seasons, atmosphere;
  `orbit` = moon phases, eclipses, year/seasons, tides; `molecules` = heat, boiling,
  evaporation, melting, gas pressure, diffusion; `atom` = atoms, electricity, magnets at atomic
  level; `waves` = sound, water waves, vibration, echoes. Never use a preset outside its topics
  (no Earth/orbit in a kitchen topic, no atom in a sky topic).
- Kitchen, home and machine topics (cooker, fridge, fan, bulb, mirror, magnet, cycle) get a
  **custom `code`** 3D model of that very object, or no 3D at all.
- If no 3D view would make the idea clearer, **skip 3D**: a good 2D SVG scene is better than an
  unrelated 3D one. At most two 3D scenes per video.
- Write one line in the storyboard per 3D visual: `"why": "<how this 3D shows the concept>"`.
  If you cannot write it honestly, do not use that 3D scene.
- On the preview sheet: object centred, not too dark, labels not cut off.

## 2d. Title and caption keywords (reach)

The title decides whether people find and tap the video. Write it for search first, curiosity second.
- **Keyword first:** start with the exact words people type when they wonder about this, in
  Roman-script Hinglish, e.g. "Aasmaan neela kyun hota hai?", "Pressure cooker mein khana jaldi
  kaise pakta hai?". Put the main keyword in the first 40 characters (that is all the Shorts feed
  shows). Use search words: kyun, kaise, kya hai, sach ya jhooth, plus the topic noun.
- **Then a curiosity hook:** a short tease of the surprise or payoff, e.g. "| Asli wajah hairaan
  kar degi", "| 99% log galat sochte hain" (only if the video really shows that people get it
  wrong). Never promise something the video does not deliver; no fake numbers.
- **Then a broad keyword + #shorts:** e.g. "Science in Hindi #shorts". Whole title under 70
  characters; at most one emoji; no ALL CAPS sentences.
- **Before writing,** do one web search for the topic phrased as a question to see how people
  word it (e.g. Hindi/Hinglish search results, Quora-style questions) and match that wording.
- **Vary the pattern** day to day; check the last 7 titles in `topics/used.csv`/storyboards so
  titles do not all look the same.
- **Description / caption:** first line repeats the keyword title (Instagram search reads the
  caption), then 2-3 Hinglish lines with one related keyword phrase (e.g. "rayleigh scattering
  hindi"), the comment question, and 4-6 hashtags: `#shorts` (YouTube only), `#science`,
  `#scienceinhindi`, `#hindifacts`, plus 1-2 topic tags. Avoid huge irrelevant hashtag lists.
- **YouTube tags:** 6-10 tags mixing Hindi and English search phrases for the topic
  (e.g. "aasmaan neela kyun", "why is sky blue in hindi", "science facts hindi").
- **Engagement keywords** (genuine prompts that make people act; vary them daily):
  - **Say the keyword in the first spoken sentence** and show it in the hook headline: both
    platforms read speech and on-screen text for search, and viewers know at once the video
    answers their question.
  - **Comment trigger:** end the narration and the caption with a specific, easy question about
    the viewer's own life or a quick A/B choice ("Aapke ghar mein cooker ki kitni seeti? 2 ya 3?",
    "Sach ya myth? Comment karo"). One question, answerable in one word.
  - **Save trigger:** one line that makes the video worth keeping ("Save karo, exam mein aayega!",
    "Save karo, next time mummy se bahas jeetoge").
  - **Share trigger:** a playful tag line ("Us dost ko bhejo jo kehta hai chaand diet par hai").
  - **Follow line:** "Roz ek naya 'aisa kyun?' — follow karo @bablu.masterji".
  - **Power words** in title/caption, only when true: "asli wajah", "sach", "myth", "99% log galat",
    "pehli baar", "exam mein aayega", "1 minute mein". Never invent claims to sound exciting.
  - **Avoid engagement bait** that platforms push down: "like karo agar...", "comment YES",
    "tag 10 friends", "share nahi kiya to...". No more than one save, one share and one
    comment prompt per caption.
  - **First comment** (posted right after publishing, see steps 4 and 4b): a bonus quiz question
    on the same topic with options, e.g. "Bonus sawaal: chaand ka kitna hissa hamesha roshan
    rehta hai? A) Poora B) Aadha C) Kuch nahi". It starts the comment thread.
- Save the final title in the storyboard as `"post_title"` so tomorrow's run can see recent titles.

**Background music:** the channel tune is `funky` (the user's choice; it is the default, so leave
`music_style` out). Each video automatically gets its own tempo, key and hook. Do not switch to
another style unless the user asks.

## 3. Quality gates (all must pass to post automatically)

- The hook and mechanism scenes are living SVG scenes (3+ moving parts each, step 2c).
- Every 3D scene shows today's topic (its `why` line is true) and renders (no `PAGE ERROR`).
  An unrelated 3D scene fails the gate: replace it with a related one or with 2D.
- The script has a funny hook, at least 2 more funny lines (one in the narration) and a funny
  comment question at the end.
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
   `video_url` = PUBLIC_URL, `caption` = keyword title as the first line, then the caption
   built by step 2d (comment question + "Present" + 4-6 hashtags), `share_to_feed` = true,
   `thumb_offset` = milliseconds of the hook frame (first beat's audio end from
   `work/timeline.json`, times 1000).
3. Then post the bonus quiz question as the first comment: `execute_action` with action
   `create_comment` (params `media_id` = the new post's id, `message` = the question).
   A failed comment never blocks the post; just mention it in the report.
4. If the script printed `UNVERIFIED` and Windsor says the video URL could not be fetched,
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
   - `text` = the YouTube description built by step 2d (keyword first line, 2-3 Hinglish lines,
     hashtags starting `#shorts`)
   - `youtubeData`: `title` = the keyword title from step 2d (under 70 characters, ends with `#shorts`), `type` `short`,
     `privacy` `public`, `category` `EDUCATION`, `madeForKids` **false** (user's choice),
     `isAiGeneratedContent` false (animated cartoon, not realistic), the 6-10 `tags` from step 2d
   - `firstCommentText` = the same bonus quiz question (if Metricool rejects it, post without it)
   - `publicationDate` `{dateTime, timezone: "Asia/Calcutta"}` matching `date`
3. Wait about 7 minutes, then `getScheduledPosts` for today: the YouTube provider should show
   `status` `PUBLISHED` with a `publicUrl`. If it shows an error, do not retry more than once;
   tell the user.

## 4c. Post to Facebook Reels (Windsor.ai), when a Page is connected

Only if the quality gates passed. Uses the same PUBLIC_URL as step 4.
1. Windsor `get_connectors` (include_options false): if `facebook_organic` has no `accounts`,
   skip this step and add one line to the report: "Facebook: Page not connected yet". Do not
   ask the user to connect it more than once a week (Mondays).
2. Otherwise `execute_action` connector `facebook_organic`, account = that Page's id (connected
   22 Nov 2026: Page "Bablu Masterji", id `1473702775829521`), action
   `create_reel`, params `{"video_url": PUBLIC_URL, "description": <the Instagram caption>}`.
   Report the returned post id. If it fails, retry once after 2 minutes, then report the error.

## 5. Log and report

1. Append to `topics/used.csv`: `date,slug,topic,status,instagram_media_id,youtube_url`
   (status `posted`, `held` or `post_failed`; leave a field empty if that platform failed). Commit the storyboard and the log to `main`
   with message `short: <date> <slug>` and push.
2. Send the user (SendUserMessage + SendUserFile) the MP4 and cover, with:
   - whether it went live on Instagram and YouTube (with the YouTube Shorts link),
   - any approximate number to double-check, and a note that you cannot hear the audio.
   - **Channel performance** (from the `stats` branch, refreshed daily at 14:15 IST by the
     `youtube-stats` workflow with the read-only `YOUTUBE_API_KEY` secret):
     `git fetch --depth 1 origin stats && git show FETCH_HEAD:stats.json`. Report yesterday's
     Short (views, likes, comments) and the best Short of the last 7 days, in 2-3 short lines.
     Channel totals can lag on YouTube; trust the per-video numbers. If `ok` is false or the
     branch is missing, skip this part and mention it in one line.
   - **Milestones** (one line daily, a short table on Mondays): YouTube subscribers and
     `views_90d` from `stats.json` against 500 subs + 3M Shorts views/90 days (fan funding) and
     1,000 subs + 10M Shorts views/90 days (ads; rises to 20M for new applicants from
     1 Feb 2027); Instagram followers via Windsor `get_data` (connector `instagram`, account
     `bablu.masterji`, field `followers_count`, date_preset `last_1dT`) against 500 (Gifts),
     1,000 (Creator Marketplace, brand deals) and 10,000 (Subscriptions). Show percent reached.
   - **Mondays only:** one line of human-touch advice for the owner from the week's comments
     (e.g. "reply to these 3 comments", "pin the best answer"), since real interaction also
     shows the channel is not mass-produced.

Keep the report short: the user reads it on a phone.
