# Storyboard format

A storyboard is one JSON file. `examples/pressure_cooker.json` is a complete example.

## Contents
1. Top level
2. Scene
3. Beat (voice, mascot, timing)
4. Screen layout
5. Built-in visuals
6. Custom SVG / HTML visuals and animation attributes
7. Troubleshooting

## 1. Top level

```json
{
  "title": "Cooker mein khaana jaldi kyun pakta hai?",
  "handle": "@bablu.masterji",      // shown top right
  "mascot": "masterji",             // default; "robot" = old robot mascot
  "voice": "hi-IN-MadhurNeural",    // or hi-IN-SwaraNeural
  "rate": "+6%",                    // speaking speed
  "music": 0.05,                    // background pad volume, 0 = off
  "captions": true,                 // Hindi captions under the visual
  "scenes": [ ... ]                 // 5-7 scenes
}
```

## 2. Scene

```json
{
  "color": "cyan",                  // accent: cyan | pink | amber | green | violet | red  (vary per scene)
  "kicker": "Pehle yeh samjho",     // small label above the headline (optional)
  "headline": "Paani *100°C* par ruk jaata hai",   // *...* = highlighted in the accent colour
  "sub": "One or two short lines.", // optional
  "visual": { "type": "...", ... }, // see sections 5 and 6
  "beats": [ ... ]                  // 1-4 beats
}
```

Headline and sub shrink automatically if long, but short text looks better: headline up to 2 lines,
sub up to 2 lines. Skip `sub` when the visual already says it.

## 3. Beat

A beat is one voice clip plus what the mascot does during it. Beats are numbered from 0 inside
each scene, and visual elements appear on a beat number (their `step`).

```json
{
  "say": "खुले बर्तन में पानी सौ डिग्री पर उबलने लगता है।",  // Hindi narration, numbers as words
  "caption": "…",          // optional: caption text if it should differ from `say`
  "pose": "point",         // idle | point | think | shock | happy | sad | shrug | wave (Masterji props follow the pose)
  "bubble": "bas 100 tak?",// mascot speech bubble, about 4 words (optional)
  "friend": "seeti = alarm?", // purple friend's bubble; the friend appears in any scene that uses this
  "friendPose": "think",
  "pause": 0.4,            // extra silence after this beat (optional)
  "hold": 1.5              // length of a beat with no `say` (optional)
}
```

Timing is automatic: each beat lasts as long as its voice clip plus a short gap. `step: 0` elements
appear as the scene opens; `step: 1` elements appear when beat 1 starts, and so on.

## 4. Screen layout (1080 x 1920)

| Area | Position | Notes |
|---|---|---|
| Progress bar + handle | y 84-140 | one segment per scene |
| Kicker, headline, sub | y 186-580 | centred |
| Visual | x 60-1020, y 600-1130 (960 x 530) | components or custom SVG |
| Hindi caption | y 1150-1260 | automatic |
| Mascots + bubbles | y 1270-1620 | automatic |
| Bottom 300 px | empty | Instagram and YouTube draw their own buttons and caption here |

## 5. Built-in visuals

All accept `"tag": "small footnote"` (for example a source or "illustrative numbers").
`color` is an accent name or any CSS colour. `step` is the beat on which the item appears.

**compare** - two panels side by side. Best for before/after, myth/fact, A vs B.
```json
{"type":"compare","vs":true,
 "left": {"icon":"🍲","title":"Khula bartan","lines":["Dal: ~40 min"],"color":"cyan","step":0},
 "right":{"icon":"⏱️","title":"Pressure cooker","lines":["Dal: ~10 min"],"color":"amber","step":1}}
```

**bars** - 2 to 4 vertical bars that grow while the number counts up.
```json
{"type":"bars","unit":"°C","max":130,"decimals":0,
 "items":[{"label":"Khula bartan","value":100,"color":"cyan","step":0},
          {"label":"Cooker","value":120,"color":"amber","step":1}]}
```

**number** - one huge counting number. Best for a single striking figure.
```json
{"type":"number","from":25,"to":100,"suffix":"°C","prefix":"","decimals":0,
 "label":"Khule bartan mein paani ki limit","color":"cyan","step":0}
```

**cards** - 2 to 4 cards in a row, each with an emoji icon, a small label and a value.
`"on": true` gives a card a glowing border; `"dim": n` fades it on beat n; `"hide": n` removes it.
```json
{"type":"cards","items":[
  {"icon":"🔒","label":"Step 1","value":"Bhaap band","color":"pink","step":0},
  {"icon":"🔥","label":"Step 3","value":"120°C","color":"green","step":1,"on":true}]}
```

**list** - up to 4 numbered rows that slide in. Best for steps, choices, reasons.
If `step` is left out, row k appears on beat k.
```json
{"type":"list","items":[
  {"title":"Seeti upar uthti hai","note":"raasta khulta hai","color":"amber","step":1}]}
```

Emoji render in colour and are fine as icons. Keep text inside components short; the layout check
reports overflow.

## 6. Custom SVG / HTML visuals

Use these for the mechanism scene, where a drawing of the actual thing (a cooker, the Moon and
tides, a lung, a wire with electrons) explains more than bars or cards.

```json
{"type":"svg","svg":"<svg viewBox='0 0 960 530' xmlns='http://www.w3.org/2000/svg'> ... </svg>"}
```

- Draw in a `viewBox` of `0 0 960 530`. Use single quotes for attributes so the JSON stays valid.
- An SVG visual gets a faint rounded panel behind it; `"panel": false` removes it.
- Make the subject large: the main object should fill at least half the box. Use strokes of 5-8 px
  and text of 24 px or more, or it will be unreadable on a phone.
- Colours that match the theme: cyan `#35d6ed`, pink `#ff5c8a`, amber `#ffb020`, green `#43e08c`,
  violet `#a78bfa`, light `#dfe4ee`. Text classes: `lbl` (small mono label), `t-big`, `t-mid`, `t-sm`.
- `{"type":"html","html":"..."}` works the same way with HTML inside the 960 x 530 box.

### Animation attributes

Put these on any element (usually a `<g>`). All timing is computed per frame from the video
clock, so CSS animations and `<animate>` tags will not work; use these instead.

| Attribute | Meaning |
|---|---|
| `data-step='n'` | appear when beat n starts (0 = as the scene opens) |
| `data-anim='…'` | how it appears: `fade`, `up`, `pop`, `left`, `right`, `grow` (rises from its base), `growx` (extends from its left edge), `draw` (a stroked path draws itself) |
| `data-delay='0.3'` | seconds after the beat starts |
| `data-dur='0.8'` | entrance length in seconds |
| `data-hide='n'` | fade out when beat n starts |
| `data-dim='n'` | drop to low opacity when beat n starts |
| `data-count='from,to,decimals'` | text counts between two numbers; add `data-prefix`, `data-suffix` |
| `data-loop='…'` | continuous motion: `pulse`, `float`, `spin`, `shake`, `blink`, `rise` (drifts up and fades, repeat; set `data-phase='0..1'` and `data-dist='120'` to stagger particles) |

Rules that avoid surprises:
- An element with `data-step`, `data-anim` or `data-loop` has its CSS transform controlled by the
  engine, so do not also give that element a `transform` attribute. Wrap it: put the `transform`
  on an outer `<g>` and the data attributes on an inner one.
- To combine an entrance with a loop, nest them: `<g data-step='1' data-anim='pop'><g data-loop='pulse'>…</g></g>`.
- `draw` needs a `<path>`, `<line>` or `<polyline>` with a stroke and `fill='none'`.

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `LAYOUT: header text runs into the visual` | shorten headline or sub |
| `LAYOUT: visual content overflows` | fewer items or shorter labels |
| `PAGE ERROR` or the page fails to start | broken SVG markup or a double quote inside the `svg` string |
| Total too long / short | cut or add a sentence; each Hindi word is roughly 0.4 s |
| Voice blocked, want to see layout | `--check --tts silent` (estimated timing, preview sheet only) |
| A word is mispronounced | respell it phonetically in `say` and keep the right spelling in `caption` |
| Voice engine falls back to the Google voice | Microsoft's service was unreachable; rerun later for the better voice |
