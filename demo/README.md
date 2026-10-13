# Demo Video

**Status: to be recorded** – the video is the single most convincing piece of
evidence for a GitHub profile / job interview, because a commercial RPA tool
cannot be run by the reviewer.

## What to record (1-2 minutes, recommended script)

1. **Intro (5s)** – open the project in VS Code, show `README.md` headline.
2. **Python pipeline (40s)** – run `python run_demo.py` in the terminal;
   narrate: orders ingested → cleaned → report generated.
3. **Report (20s)** – open the generated `.xlsx`; point at the `Summary` sheet
   (KPIs) and the `Quality Report` sheet (dirty data removed, issue counts).
4. **Alerting demo (25s)** – run `python run_demo.py --fail-once` twice, then
   show the alert email (or the log message when SMTP is not configured).
5. **Yingdao (optional, 20s)** – open the Yingdao client, show the
   `order_crawl` flow diagram, run it once.

## Tools

- Screen recording: **OBS Studio** or **Xiaomi/Windows Game Bar** (`Win+G`)
  – or the recorder built into JianYing (剪映), which you already use.
- Keep the video under 2 minutes; `H.264 + AAC`, 1080p, ~10 MB.

## After recording

1. Put the file at `demo/demo_video.mp4` (kept out of git via `.gitignore`).
2. Host it on GitHub Releases or an unlisted cloud link.
3. Link it from `README.md` (replace the placeholder paragraph).
