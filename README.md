# news-image-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/ayubzoel/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/ayubzoel/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

A program that draws one 1024×1024 poster summing up the world news of Saturday, 21 November 2026 — the APEC trilateral in Shenzhen, the Iran–US standoff over the Strait of Hormuz, the COP31 deadlock, the AI stock sell-off and more — as a single newspaper-style image with a numbered world map.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

This writes `out/entry.png` (1024×1024, under 1 MiB). The program uses only the Python standard library and Pillow, makes no network requests, and is deterministic: running it twice produces byte-identical output.

---

<sub>Entered on [make.fun](https://make.fun/?ref=v916a3tf&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>
