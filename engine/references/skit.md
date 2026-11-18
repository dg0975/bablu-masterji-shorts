# Skits ("Masterji ki Class" comedy + science punchline)

A skit is a storyboard with `"kind": "skit"`. It reuses the voice, timing, music and render code of
`make_short.py`, but draws full-screen sets with several characters (`assets/skit.html`).
Status: **scheduled** Tue/Thu/Sat, run starts 18:21 IST (posts about 6:30-7:00 PM), following
`SKIT_RUN.md`; first run (Thu 19 Nov 2026) posts the approved demo. Voices approved by the owner:
Golu `kunal_hi_kids` pace 1.4, Mummy `roopa_hi_conversational`, Papa `ashok_hi_character` pace 1.5,
Masterji = channel voice.

Shape that works: 25-40 s, 5-7 shots, one relatable desi situation (home or class), a wrong idea
from Golu, Mummy/Papa reaction, Masterji explains in 2 short lines, Golu's punchline, ending card
with the checked science fact and a comment question. Same rules as the explainers: fact-checked,
original jokes, family-friendly, no real people or brands, varied from earlier skits.

## Top level
```json
{"kind":"skit","series":"MASTERJI KI CLASS","title":"Golu ka garmi wala jugaad","handle":"@bablu.masterji",
 "post_title":"...","tts":"sarvam","lead":0.15,"gap":0.2,"outro":1.4,
 "music_style":"funky","music":0.16,"duck":0.65,
 "cast":{"golu":{"name":"Golu","voice":"kunal_hi_kids","pace":1.4},
         "mummy":{"name":"Mummy","voice":"roopa_hi_conversational"},
         "papa":{"name":"Papa","voice":"ashok_hi_character","pace":1.5},
         "masterji":{"name":"Masterji"}},
 "scenes":[ ...shots... ]}
```
`cast.<id>.voice` / `pace` = Sarvam speaker and speed for that character (Masterji uses the
channel voice). A beat may override with `"voice"`. Render with
`make_short.py <skit>.json --out work --tts sarvam --voice-dir work/voice --min 15 --max 40`.

## Shots (`scenes`)
```json
{"set":"kitchen","board":"(classroom only: chalkboard text)","scale":0.78,
 "cam":{"zoom":1.7,"on":"mummy","push":0.05},
 "cast":[{"id":"golu","x":220,"pose":"sly","enter":"left"},{"id":"mummy","x":540},{"id":"papa","x":860}],
 "card":{"kicker":"Science ka sach","text":"...","foot":"comment question"},
 "beats":[ ... ]}
```
- `set`: `classroom`, `livingroom`, `kitchen`. Characters: `masterji`, `golu`, `mummy`, `papa`.
- `x` = centre on the 1080-wide frame; 3 people: x 220/540/860 with shot `"scale":0.78`; 2 people: `0.9`.
- `enter`: `left`, `right`, `pop`, `drop`. `flip:true` mirrors a character.
- `cam.on` = character id (close-up on the face) or `[x,y]`; `zoom` 1-2; `push` slow zoom-in.
- `card` shows the end card (use on the last shot).

## Beats
```json
{"who":"golu","say":"Devanagari line","caption":"optional subtitle text",
 "act":{"golu":"happy","papa":"facepalm"},"hop":["golu"],"shake":true,
 "fx":{"kind":"bulb","on":"masterji"},"sfx":"ding","cam":{"zoom":1.5,"on":"masterji"}}
```
- A beat without `say` needs `"hold": seconds` (reaction or dance moments).
- Poses: idle, talk, shock, happy, laugh, angry (Mummy's belan), sad, point, think, sly, dance,
  hand (raise hand), facepalm, hold (Papa's newspaper), wave. Masterji also uses his own poses.
- `fx`: bulb (idea), sweat, question, stars, anger, hearts, pop (`"text":"DHADAAM!"`), lines (speed lines).
- `sfx` (made in code): boing, ding, whoosh, drum (ba-dum-tss), pop, crash, bell (school bell),
  slide (slide whistle), scratch. List form: `[{"s":"boing","at":0.3,"gain":0.8}]`.
- Voices are trimmed of long silences automatically; slow voices can be sped up with `pace`.
