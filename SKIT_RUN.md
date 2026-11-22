# Skit run: one "Masterji ki Class" comedy short, every evening

This file is the instruction set for the skit scheduled task. Each run is a fresh Claude session;
everything it needs is in this repo. **Since 21 Nov 2026 the skit is the channel's only daily post**
(owner's choice: evenings work best). The run starts 18:21 IST and the post goes live about
6:30-7:00 PM IST. The 3 PM explainer (DAILY_RUN.md) is paused; DAILY_RUN.md still holds the posting,
monetisation and report rules this file points to.

Channel: @bablu.masterji. Format: 20-28 s comedy with a science punchline (owner decision 22 Nov 2026,
see 2c). Read
`engine/references/skit.md` (format, sets, cast, poses, fx, sfx) and the demo
`storyboards/2026-11-18-skit-fridge-jugaad.json` before writing.

## 0. Setup
1. Attach and clone this repo with push access: `dg0975/bablu-masterji-shorts`.
2. Read `engine/SKILL.md`, `engine/references/skit.md`, and DAILY_RUN.md sections 1b (stay
   monetisable), 2b (humour), 2d (titles and engagement), 4, 4b and 5 (posting and reporting);
   those rules apply to skits too, except where this file says otherwise.

## 1. Pick the skit
- Read `topics/skits_used.csv`. **If `fridge-jugaad` is not in it, this run posts the approved
  demo `storyboards/2026-11-18-skit-fridge-jugaad-gemini.json` unchanged** (copy it to
  `storyboards/<today>-skit-fridge-jugaad.json`), then go to step 3.
- **Else, if `dadi-matka` is not in it, post the ready demo `storyboards/2026-11-21-demo-skit-dadi-matka.json`
  unchanged** (copy it to `storyboards/<today>-skit-dadi-matka.json`), then go to step 3.
- Otherwise take the first unused idea from `topics/skit_ideas.md` (or a fresher everyday idea
  with a solid science fact). Never repeat a skit or its punchline.
- **Keep the queue full (daily posting uses it fast):** if fewer than 10 unused ideas remain, add
  8-10 new ones to `topics/skit_ideas.md` in the same one-line format (slug: situation with the
  cast; the checked science fact), mixing the extra cast, sets and science areas (heat, light,
  sound, forces, body, plants, kitchen chemistry, space), and commit them with the run.
- **Stay original day after day (YouTube "inauthentic content"):** never the same set + cast
  combination as yesterday, never the same opening gag shape twice in a week, rotate who wins the
  argument, and change the end-card question style (A/B choice, "aapke ghar mein kaun...",
  quiz). Follow DAILY_RUN.md 1b's never-list and labels.
- Fact-check the science fact with web search; if unsure, pick another idea.

## 2. Write the skit
- 20-28 s, 4-6 shots: relatable desi moment, Golu's wrong idea or jugaad, Mummy/Papa reaction
  (belan, newspaper, facepalm), Masterji's 2 short lines explaining the science, Golu's punchline,
  ending card (`card`) with the checked fact and a one-word comment question.
- **Voices: Google Gemini for everyone in a skit, Masterji included (owner feedback 20 Nov: voices must fit the
  characters and move fast).** Use exactly this cast:
  `"cast":{"golu":{"name":"Golu","engine":"gemini","gvoice":"Zephyr","style":"a cheeky 10-year-old Indian boy, excited and mischievous"},"mummy":{"name":"Mummy","engine":"gemini","gvoice":"Kore","style":"an Indian mother scolding her son, loud, dramatic and annoyed"},"papa":{"name":"Papa","engine":"gemini","gvoice":"Algenib","style":"a tired Indian father, dry and sarcastic"},"masterji":{"name":"Masterji","engine":"gemini","gvoice":"Charon","style":"Masterji, a funny and warm Indian school teacher in his 50s, confident, lively and clear"}}`
  When a skit uses the extra cast, add them with these Gemini voices (keep them the same every time):
  `"dadi":{"name":"Dadi","engine":"gemini","gvoice":"Gacrux","style":"a loving, witty Indian grandmother, warm and a little teasing"}`,
  `"pinky":{"name":"Pinky","engine":"gemini","gvoice":"Leda","style":"a sarcastic teenage Indian elder sister, bored and unimpressed"}`,
  `"bunty":{"name":"Bunty","engine":"gemini","gvoice":"Erinome","style":"a polite know-it-all 11-year-old topper boy, precise and a bit smug"}`,
  `"aunty":{"name":"Sharma Aunty","engine":"gemini","gvoice":"Laomedeia","style":"a nosy, gossipy neighbour aunty, loud and dramatic"}`.
  Sarvam fallback for them: Dadi `roopa_hi_narration`, Pinky `kavya_hi_conversational`,
  Bunty `aayan_hi_conversational`, Aunty `simran_hi_social_excited`.
  **Act every family line:** add a beat-level `"style"` describing the emotion of that moment
  ("shouting angrily", "embarrassed and sheepish", "thrilled, laughing"), and use at most one
  inline English tag in `say` where it fits: `<laugh>`, `<sigh>`, `<gasp>`, `<short pause>`.
  Keep the rest of `say` a clean spoken line (no stage directions); subtitles hide the tags.
  Never write "slow" or "calm" in a style: the engine adds a sitcom-pace instruction to every Gemini line.
  **Automatic polish (make_short.py + voice_fx.py, nothing to set):** pauses inside a line are
  squeezed, slow lines are sped up to comedy pace (up to x1.32), Golu and Bunty are pitched to a real
  kid's voice, every character is EQ'd, compressed and loudness-matched, and mouths lip-sync to the
  actual sounds (closed m/b/p, open aa, wide ee, round o/oo, teeth s/f). Check the `[voice]` lines
  in the render log; a kid line with `pitch x1.4+` or any `polish failed` line is worth mentioning.
- **Pace:** reaction beats (`hold`) are capped at 0.75 s and lines follow each other with a 0.08 s
  gap. Keep `hold` at 0.5-0.75. Don't set `gap`/`lead`.
- **Camera:** leave `cam` out on most beats. The auto camera cuts to a close shot of whoever speaks
  (alternating framing), goes wider for group reactions, with a slow push-in and slight handheld
  drift. Use an explicit `cam` only for a special moment (a big reveal or slow push).
  The voice job tries the backup Gemini key (`GEMINI_API_KEY_2` secret) by itself when the main key
  fails or hits its quota; `status.json` shows `gemini_key` 1 or 2 (mention 2 in the report).
  **Fallback:** if `get_voice.sh` reports a Gemini error with every key (quota, rate limit, model), replace the
  cast with the Sarvam cast `"golu":{"voice":"kunal_hi_kids","pace":1.4}`,
  `"mummy":{"voice":"roopa_hi_conversational"}`, `"papa":{"voice":"ashok_hi_character","pace":1.5}`
  (keep the names), push again, re-run `get_voice.sh`, and mention the fallback in the report.
  plus `"tts":"sarvam","outro":0.7,"music_style":"funky","music":0.16,"duck":0.65`.
- Lines are short spoken Hindi in Devanagari, about 6-12 words each. Funny but family-friendly: roast situations, never groups; Mummy's belan is a joke
  prop, never actual hitting. No real people, brands or other creators' characters or songs.
- Vary sets, shot order and gags from the last 3 skits. Save `"post_title"` and `"format":"skit"`.
- **Cast:** use at least one of the extra cast (Dadi, Pinky, Bunty, Sharma Aunty) in every skit,
  rotating them; Golu, Mummy and Papa are not needed every time. Props for the gag: scene
  `"props":[{"kind":"matka","x":150,"y":1300,"scale":1.1}]` or a held `"item"` on a cast member
  (`bottle`, `glass`, `chai`, `matka`; change per beat with `"item":{"golu":"glass"}`).
- No "..." inside `say` (Gemini turns it into a long pause); use a comma.

## 2a. Joke quality (write the jokes first, the science second)

A skit is judged on its laughs. Before writing JSON, write the 3 jokes in plain text and check each
against these rules; rewrite any that fail.
1. **Three laughs minimum:** an opening gag in the first 3 s, a mid-skit topper, and the final
   punchline. Plus one visual gag (prop, reaction, fx) that works with the sound off.
2. **Setup, then misdirect, then punch.** The listener expects one thing, the last words flip it.
   Put the punch word **at the very end** of the line ("...सदर बाज़ार से।"), never explain it after.
3. **Callback ending:** the best final punchline reuses something from the first 10 s in a new
   way (Bunty's "imported" bottle "from Sadar Bazaar" -> Dadi: "सदर बाज़ार हार गया"). Plan the
   ending first, then plant its setup early.
4. **Character-driven, not random:** each joke comes from who they are. Golu's confident wrong
   logic, Bunty's showing off getting punctured, Dadi's old-school wisdom winning, Pinky's
   deadpan roast, Sharma Aunty's dramatic half-truths, Papa's dry money jokes, Mummy's threats.
5. **Specific desi detail beats generic:** "धूप में रखी लस्सी", "सदर बाज़ार", "बिजली का बिल",
   "चार्जर कहाँ है" are funnier than "very hot" or "cheap shop". One concrete image per joke.
6. **Escalate:** each beat raises the stakes or the absurdity; no two jokes of the same type in a row.
7. **The underdog wins** (kid, Dadi, the "uneducated" idea) and the show-off loses; punch up,
   never at a group, body, region, caste, religion or disability.
8. **Short lines hit harder:** punch lines 3-8 words; setups up to 12. One idea per line.
9. **Reaction after every punch:** give the next beat (or a 0.5-0.75 s `hold`) to a reaction
   (`facepalm`, `laugh`, `shock`) with an `sfx` (`drum` for roasts, `scratch` for awkward reveals).
10. **Science stays true and short:** Masterji explains in 2 lines max, the joke never bends the
    fact, and the last word belongs to a character's punchline, not the lecture.
Self-check before pushing: read the lines aloud in order; if a line would not get even a smile from
a 12-year-old or a parent, cut or rewrite it. Report the 3 jokes in the run report.

## 2b. Relatable first (lessons from studying successful desi comedy Shorts)

Format research on a desi cartoon-comedy channel (public stats of its last 100 Shorts, Nov 2026;
studied for patterns only, never copy anyone's characters, jokes, scripts or songs):
- The best performers are **instantly relatable family moments**: the Indian mother, family
  drama, money/"gareeb" jokes, friends, office/boss, childhood memories, railway, chai. Lead with
  a situation every Indian viewer recognises within 2 seconds, then deliver our science twist.
- **Open on the joke**, not on setup: first shot already shows the funny situation.
- **Reaction close-ups** (deadpan parents, shocked faces) carry the laugh; use at least one.
- **Titles are short and emotional**, 2-5 words plus one emoji, e.g. "Golu ka jugaad 😂",
  "Mummy vs Fridge 😤", then `#funny #relatable` and one science tag. The search keyword goes in
  the first line of the description instead (DAILY_RUN.md 2d still applies to descriptions).
- Recurring cast helps people come back: keep every personality consistent. Golu: jugaadu and
  overconfident. Mummy: strict, belan, always right. Papa: dry, sarcastic, newspaper. Dadi: loving,
  sharp, old-school wisdom that is often right, walking stick. Pinky: Golu's elder sister, glued to
  her phone, roasts him. Bunty: the neighbour's perfect topper ("Bunty ko dekho!"), glasses, books;
  sometimes he is wrong too. Sharma Aunty: nosy neighbour who spreads half-true "facts" Masterji
  corrects. Use 2-3 characters per skit, rotate who appears; Masterji explains the science.
- Sets: classroom, livingroom, kitchen, train (trees rush past the windows), tapri (street chai
  stall), terrace (water tank, washing line, kite), bedroom (`"night":true` for a night window).

## 2c. Reach rules (owner decision 22 Nov 2026, from the channel's own numbers)

Week-1 data: skits got about 10x the views of explainers, but on Instagram 35-60% of viewers swiped
away in the first 3 s, the average watch was only 7-13 s of 30-40 s videos, and shares/saves were
almost zero. These rules fix that; every skit must follow them:
1. **Hook on frame 1.** Set `"hook"`: a 3-7 word Hinglish line shown big from the first frame
   (the render refuses a skit without one), with one `*highlighted*` word, e.g. "Golu ne kamre ka
   *AC* bana diya?", "Dadi vs *Topper*: kaun jeeta?". It must tease the conflict, not the answer.
2. **Cold open.** Shot 0 starts mid-action with the funniest/most surprising line: no entrances
   (`enter` is refused in shot 0), no greeting, no setup line; the first spoken line is at most 6
   words and lands on frame 1. Entrances are fine from shot 1 on.
3. **20-28 s total** (render with `--max 30`). Cut anything that does not set up or land a joke;
   Masterji gets one or two short lines. Short videos get watched to the end and replay.
4. **Loop ending.** The last line should flow back into the first frame (e.g. ends on a question
   the opening line answers, or Golu starting the same jugaad again), and `outro` stays 0.7 so the
   loop comes quickly. Keep the end card short (`text` up to about 18 words).
5. **Built to be sent.** Pick situations people tag friends and family in ("har ghar mein ek Dadi
   hoti hai", the topper cousin, the AC fight, the chai uncle). End the caption with one natural
   share line naming a character type: "Apne Bunty dost ko bhejo 😂", "Ghar ke Golu ko tag karo".
   Not "like/share/subscribe" bait.
6. **Series with part numbers.** Every skit belongs to one series, named after who drives the
   joke, and shows it as `"series"` (top-left badge): `GOLU KE JUGAAD`, `DADI KA GYAAN`,
   `PINKY KA ROAST`, `BUNTY KO DEKHO`, `SHARMA AUNTY NEWS`, `MUMMY KA RULE`, `PAPA KA BUDGET`.
   Part number = rows in `topics/skits_used.csv` with that series + 1, e.g.
   `"series":"GOLU KE JUGAAD · PART 3"`. Put "<Series>, Part N" in the post title/caption too.
7. **Facebook too.** Post the same Reel to Facebook as DAILY_RUN.md step 4c says (it skips itself
   while no Facebook Page is connected in Windsor).

## 3. Voice, check, render
1. Save to `storyboards/<YYYY-MM-DD>-skit-<slug>.json`, commit and push to `main`.
2. `bash scripts/get_voice.sh storyboards/<file>.json work/voice`
3. `python3 <engine>/scripts/make_short.py storyboards/<file>.json --out work --check --tts sarvam --voice-dir work/voice --min 15 --max 30`
   View the preview sheet: faces not cut off, effects above heads, subtitles readable, no
   `PAGE ERROR`. If the total is over 30 s, cut a line or a shot (push + get_voice again); aim for 20-28 s.
4. Full render the same way without `--check` (detached, as SKILL.md says).

## 4. Post and report
- Publish with `bash scripts/publish_pages.sh work/short.mp4 work/cover.jpg <date>-skit-<slug>`.
- Instagram via Windsor (`create_video_post`), YouTube Short via Metricool and Facebook Reel via
  Windsor exactly as DAILY_RUN.md steps 4, 4b and 4c (keyword-first title, caption ending `🎙️ AI voice · Facts: <source>`,
  first-comment quiz/question, `madeForKids` false, `isAiGeneratedContent` false).
- Caption style for skits: the short relatable title (step 2b) with the series part
  ("Golu ke Jugaad, Part 4"), then the science line, the share line from 2c, the comment
  question, 4-5 hashtags (#funny #relatable #scienceinhindi + 1 character tag + 1 topic).
- Append to `topics/skits_used.csv`: `date,slug,idea,status,instagram_media_id,series`; commit and push.
- Send the owner the MP4 and links (SendUserMessage + SendUserFile), short, phone-friendly, with:
  the skit idea and its 3 jokes, which voices were used (Gemini or the Sarvam fallback), and the
  **channel performance, milestones and Monday human-touch lines exactly as DAILY_RUN.md step 5**
  describes (yesterday's post = yesterday's skit).
