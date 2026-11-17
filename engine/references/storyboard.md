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
| more loops | `drift` (slow side-to-side, clouds; `data-dist` px, default 40), `sway` (rocks by `data-dist` degrees, trees, pendulum), `twinkle` (stars, sparkles), `breathe` (slow glow-scale, suns, hearts; `data-dist` = 0.04), `bob` (small up-down, birds, boats), `orbit` (circles `data-dist` px, molecules, electrons), `flow` (dashes stream along a stroked path: light rays, current, wind, water; give the path a `stroke-dasharray`), `glow` (soft opacity pulse) |
| `data-speed='1.5'` | speed multiplier for any loop |
| `data-phase='0.3'` | offset a loop so neighbours do not move in sync |
| `data-move='dx,dy'` | glide by dx,dy px (eased), e.g. a sun setting `data-move='0,240'`; `data-move-at` (beat, default `data-step`), `data-move-delay`, `data-move-dur` (default: to scene end) |
| `data-origin='50% 100%'` | pivot for `sway`/`spin`/`pulse` (e.g. a tree sways from its base) |

### Living scenes (the channel style since 2026-11-17)

The engine adds a drifting colour background, floating dust, a slow camera push-in with a small
punch on every beat, a light sweep between scenes, and audio-driven lip-sync and gestures for
Masterji, automatically. Your job is to make the **visual itself** feel alive:

- Draw the real thing as a small scene, not a diagram on black: a sky gradient, a sun with
  slowly spinning rays (`spin` + `data-speed='.3'`), drifting clouds, a horizon, water, a kitchen.
  Use `<linearGradient>`/`<radialGradient>` in `<defs>` for skies, glows and metal.
- **Every custom SVG has at least three things moving all the time** (loops), plus one change per
  beat (`data-step`, `data-move`, `data-hide`). Light, heat, sound, current and air are drawn as
  `flow` dashes; particles as `orbit`/`rise`; the subject breathes or bobs.
- Show change over time with `data-move` and cross-fades: a second gradient `<rect>` with
  `data-anim='fade' data-dur='3'` turns a blue sky orange; `data-hide` removes the old state.
- Keep labels at least 40 px inside the box: the camera zooms in about 4%.
- Storyboard switches: `"ambient": false` turns off background clouds and dust, `"sweep": false`
  turns off the scene-change light sweep. Leave both on for the channel.

Rules that avoid surprises:
- An element with `data-step`, `data-anim` or `data-loop` has its CSS transform controlled by the
  engine, so do not also give that element a `transform` attribute. Wrap it: put the `transform`
  on an outer `<g>` and the data attributes on an inner one.
- Loops and `data-move` also set the transform, so the same wrapping rule applies to them.
- To combine an entrance with a loop, nest them: `<g data-step='1' data-anim='pop'><g data-loop='pulse'>…</g></g>`.
- `draw` needs a `<path>`, `<line>` or `<polyline>` with a stroke and `fill='none'`.

## 6b. 3D visuals (three.js)

`{"type":"3d", ...}` fills the 960 x 530 visual box with a real-time 3D scene (WebGL, rendered
in the same headless browser). Use it for the 1-2 scenes where depth helps most: planets, orbits,
molecules, waves, a rotating object. Keep the other scenes 2D (they render faster and carry text).
Text stays in the headline/sub/captions; 3D labels are short (2-4 words).

Presets (all options optional; arrays are per beat, eased between beats):
```json
{"type":"3d","preset":"earth","rays":true,"scatterStep":1,"sunsetStep":null,"spin":0.22,
 "atmosphere":"#5fb4ff","labels":[{"text":"Neeli roshni","at":[-1.2,2.0,0],"color":"cyan","step":1}]}
{"type":"3d","preset":"molecules","speeds":[0.6,2.4],"colors":["#4aa8ff","#ff5a4e"],"count":46,
 "escapeStep":1,"escapeFraction":0.3}
{"type":"3d","preset":"orbit","focusStep":1,"earthSpeed":0.25,"moonSpeed":1.4,
 "names":{"Sun":"Suraj","Earth":"Dharti","Moon":"Chaand"}}
{"type":"3d","preset":"atom","shells":3,"nucleons":12,"speeds":[1.6]}
{"type":"3d","preset":"waves","amplitude":[0.15,0.35],"speeds":[3],"source":"point","color":"#22d3ee"}
```
- earth: Earth with clouds and glowing atmosphere; `rays` sends sunlight in from the left and,
  from `scatterStep`, part of it turns blue and scatters (sky colour); `sunsetStep` turns the
  atmosphere orange (sunsets).
- molecules: particles in a box; `speeds`/`colors` per beat show heating; `escapeStep` lets some
  fly out of the top (boiling, evaporation).
- orbit: Sun, Earth and Moon on their orbits; `focusStep` flies the camera to Earth and Moon
  (moon phases, eclipses, day/night). Labels fade during the fly-in.
- atom: nucleus with electrons on tilted orbits. waves: rippling surface (sound, water,
  vibration); `source: "line"` for straight wavefronts.
- 3D labels: keep `at` x between -2 and 2 so text is not cut off.

Custom 3D (`"code"`): a JS function body that builds the scene and returns
`(t, step, sp, lt) => {...}`, called every frame (t = video time, lt = scene time, step = beat
index, sp = seconds into the beat). Everything must depend only on these times (no
`Math.random`, no `Date`), so frames are repeatable. Available: `THREE` (r159), `scene`,
`camera`, `v` (the visual object), `H` helpers: `H.lights()`, `H.env(renderer)` (already on for
custom scenes, makes metal/plastic look real), `H.stars(n)`, `H.glow(color,size,opacity)`,
`H.label(text,{color,size})`, `H.rim(radius,color)` (atmosphere glow), `H.planetTex({seed})`,
`H.ring(radius,color)`, `H.canvasTex(w,h,draw)`, `H.stepVal(array,step,sp)`,
`H.phase(lt,speedsPerBeat)` (smooth motion whose speed changes per beat), `H.rng(seed)`,
`H.lerp`, `H.eIO`, `H.clamp`. Build shapes from three.js primitives (Cylinder, Sphere, Box,
Torus, Lathe for vessels); no external models or textures load. Example (a cooker whose weight
dances and lets out steam from beat 1):
```js
H.lights(); camera.position.set(0,1.5,6); camera.lookAt(0,0,0);
const body=new THREE.Mesh(new THREE.CylinderGeometry(1.3,1.2,1.6,64), new THREE.MeshStandardMaterial({color:0xb8c0cc,metalness:.85,roughness:.25}));
const lid=new THREE.Mesh(new THREE.CylinderGeometry(1.36,1.36,.18,64), new THREE.MeshStandardMaterial({color:0x8d96a3,metalness:.9,roughness:.3})); lid.position.y=.9;
const w=new THREE.Mesh(new THREE.CylinderGeometry(.12,.16,.35,24), new THREE.MeshStandardMaterial({color:0x222222})); w.position.y=1.15;
const g=new THREE.Group(); g.add(body,lid,w); scene.add(g);
const steam=[]; for(let i=0;i<14;i++){const s=H.glow('#ffffff',.6,.5); scene.add(s); steam.push(s);}
return (t,step,sp,lt)=>{ g.rotation.y=lt*.4; w.position.y=1.15+(step>=1?Math.abs(Math.sin(lt*14))*.06:0);
  steam.forEach((s,i)=>{const p=((lt*.6+i/14)%1); s.position.set(Math.sin(i*2.1+lt)*.2*p,1.3+p*2.2,0);
    s.material.opacity=step>=1?(1-p)*.6:0; s.scale.setScalar(.4+p*1.2);}); };
```
If the code throws, the check prints `PAGE ERROR`; fix it before rendering. A 3D video takes
about 6-8 minutes to render instead of 2-3.

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
