---
name: web-content-learner
description: Use when a user needs to download online video or audio, extract available subtitles, or transcribe media with Whisper. Do not use for generic webpage extraction, web search, or article summarization.
---

# Media Content Learner

Handle online media only. Use Browser or other web tools for ordinary pages and research.

## Commands

```bash
# Download subtitles/media and transcribe with Whisper
python3 scripts/web_content_learner.py --media "https://youtube.com/watch?v=..."

# Download without Whisper
python3 scripts/web_content_learner.py --media "URL" --download-only

# Parse a natural-language media request
python3 scripts/web_content_learner.py --input "帮我转写这个视频 URL"
```

Options: `--output`, `--model tiny|base|small|medium|large`, and `--download-only`.

## Rules

- Reject generic webpage and search requests instead of silently scraping them.
- Prefer existing subtitles when they satisfy the request; use Whisper when transcription is required.
- Confirm the output path and command result before claiming success.
- Do not print cookies, credentials, or authenticated media URLs.
- Obtain permission before downloading restricted, private, or copyrighted media beyond the user's authorized use.
