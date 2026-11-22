---
name: "hindi-shorts-maker"
description: "Turn a topic into a ~60-second vertical Hindi explainer video (Reel/Short) for @bablu.masterji, with voiceover, animated infographics and the Bablu Masterji mascot. Use when the user gives a daily short / reel topic."
---

# Hindi Shorts Maker

The user gives one topic (for example "Aaj ka topic: bijli girne par awaaz baad mein kyun aati hai"). You deliver one finished video file plus the caption text to post with it.
Style: dark background, big headline with one highlighted phrase, an animated visual in the middle,
Hindi captions, and the channel mascot **Bablu Masterji** (with an optional purple robot friend)
reacting in short Hinglish speech bubbles. Channel handle: `@bablu.masterji`. Voice is Hindi text-to-speech. Length target is 50-68 seconds. 1080 x 1920, 30 fps.

Everything is drawn by code in `assets/player.html` and rendered by `scripts/make_short.py`.
Your creative work is the storyboard: a JSON file describing scenes, narration and visuals.

## 0. Setup: get the engine files

This skill's instructions are saved on their own; the engine files come from the bundle
`hindi-shorts-maker.skill` (a zip). It contains `scripts/make_short.py`, `assets/player.html`,
`assets/fonts/` (Poppins, Kalam), `references/storyboard.md` and `examples/pressure_cooker.json`.
Use the Masterji version of the bundle: its `assets/player.html` contains `drawMasterji`. If the
bundle you find lacks it, it is the old robot-only version; ask the user for the newer file.

1. If those files already sit next to this SKILL.md, use them.
2. Otherwise look in the user's uploads for a file ending in `hindi-shorts-maker.skill` and unzip it
   into a new empty folder, e.g. `unzip -o -q <file> -d ~/hsm_src` (the files land in
   `~/hsm_src/hindi-shorts-maker/`). Copy that folder to the working directory and run from there.
3. If neither exists, ask the user to attach `hindi-shorts-maker.skill` with the topic. Do not
   rewrite the engine from memory.

Read `references/storyboard.md` and `examples/pressure_cooker.json` before writing a storyboard.
Poppins is often installed system-wide; if the fonts folder is missing the page still uses it.

**Network check (do it first, it takes seconds):** the voice needs `speech.platform.bing.com`
(Microsoft neural voice) or, as fallback, `translate.google.com` (Google basic voice). If the
check run prints `no text-to-speech engine reachable` or the proxy refuses these hosts, stop and
tell the user to add those domains to the allowed domains in their claude.ai capability settings
(web browser), then start a new chat. Never deliver a silent video.
While the voice is blocked you can still show the user a layout preview:
`python3 scripts/make_short.py storyboard.json --out work --check --tts silent` estimates timing
from word count and writes the preview sheet; the script refuses a full render in this mode.

## 1. Get the facts right first

The video states facts in a confident voice, so a wrong number gets repeated to every viewer.
- If web search is available, check the key numbers and the core explanation before writing.
- Prefer explanations found in school textbooks and well-known science sources. Avoid health claims,
  medical advice and "one weird trick" framing.
- Say "लगभग" (about) for rounded values, and put a small `tag` on the visual when numbers are
  rounded or illustrative (for example `"tag": "illustrative timings"`).
- If the popular explanation is a myth, say so. That often makes the best hook.
- Topics are public, general knowledge only: narration is sent to an external voice service, so no
  client, company-confidential or personal data.

## 2. Write the storyboard

Shape that works for 60 seconds (6 scenes, 2 beats each, about 10 s per scene):

1. **Hook** - a question or surprising contrast from daily life. No greeting, no "namaste doston".
2. **What we assume** - the everyday baseline the viewer already knows.
3. **The mechanism** - what is really happening. A custom SVG drawing usually belongs here.
4. **The payoff** - the number or comparison that answers the hook.
5. **Twist or myth** - one related thing people get wrong. The friend mascot can ask the wrong idea.
6. **Takeaway + follow** - the idea in one line, then a short call to follow.

Writing rules, and why they matter:
- **Narration (`say`) is in Hindi, Devanagari script**, simple spoken Hindi with common English
  words written in Devanagari (प्रेशर, सेफ़्टी वाल्व). Aim for 125-150 words in total; that lands
  near 60 seconds.
- **Spell numbers and units as words** in `say` ("एक सौ बीस डिग्री", not "120°C"). The voice
  reads digits and symbols unpredictably. If the caption should show digits, add a `caption` field
  to that beat.
- **One idea per beat, one sentence or two short ones.** Each beat is one voice clip, and the
  visuals advance on beat boundaries, so short beats keep picture and voice in step.
- **On-screen text is short Hinglish** (Roman script) unless the user asks for Devanagari:
  headline up to about 8 words with one `*highlighted*` phrase, sub up to about 16 words,
  speech bubbles up to about 4 words.
- **Every scene has a visual, and something visible changes on most beats.** A still screen for
  more than about 5 seconds loses viewers.
- **Living scenes:** at least two scenes (always the hook and the mechanism) use a custom SVG
  that looks like the real thing (sky, sun, kitchen, cooker, cloud) with continuous motion: see
  "Living scenes" in `references/storyboard.md`. Camera moves, background life, lip-sync and
  Masterji's gestures are automatic.
- **Give the mascot a pose on every beat** and vary them. Use `point` when the visual changes,
  `think` on questions, `shock` on surprises, `happy` on the payoff, `wave` on the last beat.
- Set `"handle": "@bablu.masterji"` in every storyboard (the user's channel).
- Do not draw other creators' characters, logos or layouts, real people or branded characters.

## Bablu Masterji, the mascot

The user's own character, designed in their "Bablu Masterji - Mascot" artifact: a funny, lovable
government-school science teacher. Strict outside, warm as chai inside. Taped-up glasses, three-hair
comb-over, three pens in the pocket and one behind the ear, a sweater vest worn twelve months a year,
chalk handprint on the belly, handlebar moustache, socks with chappals. He is drawn in code in
`assets/player.html` and is the default (`"mascot": "robot"` brings back the old robot).

Poses and props (the engine picks the props from the pose):
- `point` - pointing with the wooden ruler; use when the visual changes.
- `think` - attendance register at the belly, eyes up, "hmm"; hooks and questions.
- `shock` - hands up, the three hairs stand up, sweat drop; surprising numbers or myths.
- `happy` - cutting chai and a big smile; the payoff ("Shabaash!").
- `wave` - waving goodbye with the register; the last beat.
- `idle`, `sad`, `shrug` also work.

Speech bubbles are in his voice (short Hinglish, drawn in the handwritten Kalam font). His catchphrases,
to use sparingly (one or two per video, never the same line every day):
"Samjhe ki nahi?", "Ye exam mein aayega!" (on the key fact), "Silence! Class chal rahi hai.",
"Bilkul galat, beta!" (on a myth), "Pehle chai, phir vigyan.", "Shabaash!" (payoff), and on the last
beat "Comment mein Present lagao!" as the running attendance gag.
The purple friend (`friend` field) is still a robot; use it for the student who asks the wrong idea.

## Make it sound like a real masterji, not a robot

Text-to-speech sounds robotic mostly because of the writing. Write the narration the way a
government-school teacher actually talks to his class:
- Talk to the viewer: "बच्चों", "देखो", "सोचो ज़रा", "अब ध्यान से सुनो". One such phrase per scene at
  most, varied, never the same opener twice in a video.
- Ask, then answer: "पानी सौ डिग्री पर क्यों रुक जाता है? क्योंकि..." Questions make the voice rise
  and fall naturally.
- Short spoken sentences, 4-10 words, with commas where a person would breathe. No written-style
  Hindi (avoid "अतः", "तथा", "किंतु"; use "तो", "और", "लेकिन").
- Everyday Hinglish words in Devanagari exactly as people say them (प्रेशर, टेंपरेचर, एक्ज़ाम).
- Add `"pause": 0.4` after a question or before the key fact, so it lands like a teacher's pause.
- One small joke or teacher-ism per video ("ये एक्ज़ाम में आएगा!") in the narration, not only in bubbles.
Default voice settings (top level of the storyboard): `"voice": "hi-IN-MadhurNeural"`,
`"rate": "-2%"`, `"pitch": "-3Hz"` (slightly slower and deeper, an older man's voice).

## Humour

Every short has a funny hook, 2-3 funny lines from Masterji's character (at least one spoken)
and a funny comment question at the end. Jokes never change the fact. Family-friendly only;
roast situations, never groups or real people. (Details: the channel repo's DAILY_RUN.md, step 2b.)

## 3D

Use a `"type":"3d"` visual (three.js) only where it shows the very thing the narration explains
(never decoration; skip 3D if nothing fits), for at most two scenes where depth explains best:
presets `earth`, `molecules`, `orbit`, `atom`, `waves`, or custom `code` built from three.js
primitives. Details and an example in `references/storyboard.md` ("3D visuals").

## Stay monetisable

Vary the format (aisa-kyun, myth-vs-sach, kya-hoga-agar, ghar-ka-experiment, quiz-challenge,
3-facts), scene count, opener and catchphrase so no two videos differ only superficially; never
reuse narration lines; every video teaches one checked idea with a fresh Indian example. End
captions/descriptions with `🎙️ AI voice · Facts: <source>`. No health advice, politics,
religion, dangerous experiments, real people, brand logos, copied clips/music, or more than 5
hashtags. General audience (not made for kids).

## Skits (comedy + science punchline)

`"kind":"skit"` storyboards make 30-35 s "Masterji ki Class" comedy shorts with drawn sets
(classroom, living room, kitchen), the cast Masterji, Golu, Mummy and Papa, camera close-ups,
comic effects, sound effects and a Gemini voice with acting directions for every character
(Masterji too). The engine polishes voices automatically (comedy pace, kid pitch, loudness match),
lip-syncs mouths to the audio, draws shaded characters with real blinks and gaze, and runs an auto
camera that cuts to whoever speaks. Format and options:
`references/skit.md`. Scheduled every evening via the repo's `SKIT_RUN.md` (the only daily post since 21 Nov 2026).

## 3. Check before the long render

```bash
python3 scripts/make_short.py storyboard.json --out work --check
```

This takes under a minute. It makes the voice clips, prints each scene's length and the total,
reports layout problems, and writes `work/preview_sheet.jpg`.

- **View the preview sheet** with the Read tool. Look for clipped or overlapping text, an
  empty-looking visual, and a custom SVG that is too small or off-centre. Fix and rerun.
- If the total is outside 50-68 s, trim or add narration. Do not fix length by changing `rate` by
  more than a few percent; fast speech is hard to follow.
- Fix every `LAYOUT:` and `PAGE ERROR:` line. A page error almost always means broken markup in a
  custom SVG.

## 4. Render

A full render takes about 3 minutes, which can exceed a single command's time limit. Start it
fully detached, then poll:

```bash
setsid nohup python3 scripts/make_short.py storyboard.json --out work > work/log.txt 2>&1 < /dev/null &
sleep 45; tail -1 work/log.txt     # repeat until the log shows DONE
```

If the log stops growing and no `make_short` process is running, the render was killed: start it
again the same way. Voice clips are cached in `work/tts`, so the render reuses them.

## 5. Deliver

- Copy `work/short.mp4` to `<topic-slug>.mp4` and `work/cover.jpg` to `<topic-slug>-cover.jpg`,
  then send both to the user with the file-sending tool (SendUserFile, or `present_files` where
  that is the tool).
- In the reply, give ready-to-paste post text, written for reach:
  - **Title:** search keyword first, exactly as people type it in Roman Hinglish ("Aasmaan neela
    kyun hota hai?"), main keyword in the first 40 characters, then a short honest curiosity hook
    ("| Asli wajah hairaan kar degi") and "Science in Hindi #shorts"; under 70 characters. Check
    the usual wording with one web search; never promise what the video does not show.
  - **Caption/description:** keyword title as the first line, 2-3 Hinglish lines with one related
    keyword phrase, the comment question, and 4-6 relevant hashtags (#science #scienceinhindi
    #hindifacts + topic tags; #shorts on YouTube).
  - **YouTube tags:** 6-10 Hindi and English search phrases for the topic.
  - **Engagement wording:** say the keyword in the first spoken line; end narration and caption
    with one easy one-word question (A/B or about the viewer's life); add one save line ("Save
    karo, exam mein aayega!"), one share line ("Us dost ko bhejo jo..."), and a follow line.
    Use power words ("asli wajah", "myth", "sach") only when true. No engagement bait ("like karo
    agar", "comment YES", "tag 10 friends"). Suggest a bonus quiz question for the first comment. Mention any number that is approximate so the user can
  double-check it before posting.
- You cannot hear the audio. Say so once and ask the user to listen for mispronounced words; fix
  those by respelling the word in `say` (keep the right spelling in `caption`) and rendering again.

## Options

Voice engines: `"tts": "sarvam"` uses Sarvam AI (Bulbul) with `sarvam_speaker` (default
`harpreet_pa_narration`, Harpreet), `sarvam_model` (default `bulbul:v4-flash`) and `sarvam_pace` (default 0.97);
its clips come from `--voice-dir` (see the channel repo's DAILY_RUN.md) or from the API directly if
`SARVAM_API_KEY` is set in the environment. Otherwise the Microsoft voice is used.

Top-level storyboard fields: `voice` (`hi-IN-MadhurNeural` male, `hi-IN-SwaraNeural` female),
`rate` (default `"-2%"`), `pitch` (default `"-3Hz"`, Microsoft voice only), `music_style` (`funky` default, the channel tune: an original playful groove made in code, with
a different tempo/key/hook per video, lowered while the voice speaks; also `desi`, `lofi`,
`rotate`, `pad`), `music` (volume,
default 0.2 lively / 0.05 pad, `0` for none), `captions` (`false` hides Hindi captions), `handle` (`@bablu.masterji`),
`mascot` (`masterji` default, `robot` for the old robot).

## Limits to be honest about

- This skill makes the video. It cannot post to Instagram or YouTube; the user uploads the file.
- Auto-posting (YouTube Data API, Instagram Graph API, scheduler, approval step) is a separate,
  not-yet-built project. Keep a human approval step for factual content.
- Keep API keys and tokens in environment variables or a secrets manager, never in a storyboard
  or chat.