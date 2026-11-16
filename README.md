# Bablu Masterji Shorts

Daily 1-minute Hindi science shorts for **@bablu.masterji**, made and posted automatically.

| Folder | What it holds |
|---|---|
| `DAILY_RUN.md` | The steps the daily Claude scheduled task follows |
| `engine/` | The hindi-shorts-maker skill: render script, animation engine, Masterji mascot, fonts |
| `topics/ideas.md` | Topic queue (edit freely) |
| `topics/used.csv` | Log of every day's topic and whether it was posted |
| `storyboards/` | Each day's storyboard JSON |
| `scripts/publish_pages.sh` | Puts the day's video on GitHub Pages for Instagram to fetch |

Flow each morning: topic → fact-check → storyboard → render → quality gates → GitHub Pages →
Instagram Reel via Windsor.ai → video + YouTube text sent to the owner for the Short.

Videos live only on the `gh-pages` branch, which is replaced every day, so the repo stays small.
No passwords or API keys are stored here.
