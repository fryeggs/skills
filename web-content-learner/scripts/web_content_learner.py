#!/usr/bin/env python3
"""Download online media/subtitles and optionally transcribe with Whisper."""

import argparse
import json
import pathlib
import re
import subprocess
from typing import Callable, Optional


DEFAULT_OUTPUT = pathlib.Path.home() / "videodown"
MEDIA_HOSTS = (
    "youtube.com",
    "youtu.be",
    "vimeo.com",
    "bilibili.com",
    "twitch.tv",
    "soundcloud.com",
)
MEDIA_EXTENSIONS = (".mp3", ".m4a", ".wav", ".flac", ".mp4", ".mkv", ".webm")


def extract_url(text: str) -> Optional[str]:
    match = re.search(r"https?://[^\s]+", text)
    return match.group(0).rstrip(".,;!?)]}") if match else None


def is_media_url(url: str) -> bool:
    lowered = url.lower().split("?", 1)[0]
    return any(host in lowered for host in MEDIA_HOSTS) or lowered.endswith(MEDIA_EXTENSIONS)


def detect_intent(text: str) -> str:
    url = extract_url(text)
    if not url or not is_media_url(url):
        return "unsupported"
    lowered = text.lower()
    if any(word in lowered for word in ("download", "下载", "保存")) and not any(
        word in lowered for word in ("transcribe", "transcript", "字幕", "转写", "转文字")
    ):
        return "download"
    return "transcribe"


def whisper_transcribe(path: str, model: str) -> str:
    import whisper

    loaded = whisper.load_model(model)
    result = loaded.transcribe(path)
    return str(result.get("text", "")).strip()


class MediaLearner:
    def __init__(
        self,
        output_dir: str = str(DEFAULT_OUTPUT),
        runner: Callable = subprocess.run,
        transcriber: Callable[[str, str], str] = whisper_transcribe,
    ):
        self.output_dir = pathlib.Path(output_dir).expanduser()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.runner = runner
        self.transcriber = transcriber

    def download(self, url: str) -> str:
        template = str(self.output_dir / "%(title).120s-%(id)s.%(ext)s")
        command = [
            "yt-dlp",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            "en.*,zh.*",
            "--convert-subs",
            "srt",
            "--print",
            "after_move:filepath",
            "-o",
            template,
            url,
        ]
        result = self.runner(command, check=True, capture_output=True, text=True)
        paths = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not paths:
            raise RuntimeError("yt-dlp did not report a downloaded media path")
        return paths[-1]

    def transcribe(self, path: str, model: str = "base") -> str:
        return self.transcriber(path, model)

    def process(self, text: str, model: str = "base", download_only: bool = False) -> dict:
        intent = detect_intent(text)
        url = extract_url(text)
        if intent == "unsupported" or not url:
            return {
                "success": False,
                "error": "Only media download, subtitle extraction, and transcription are supported.",
            }

        path = self.download(url)
        result = {"success": True, "media_path": path, "intent": intent}
        if not download_only and intent == "transcribe":
            result["transcript"] = self.transcribe(path, model)
            result["model"] = model
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--media", help="Media URL")
    source.add_argument("--input", help="Natural-language media request containing a URL")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output directory")
    parser.add_argument("--model", default="base", choices=("tiny", "base", "small", "medium", "large"))
    parser.add_argument("--download-only", action="store_true", help="Skip Whisper transcription")
    args = parser.parse_args()

    text = args.input or args.media
    result = MediaLearner(args.output).process(text, args.model, args.download_only)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["success"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
