#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

EXTENSION_ID = "fgjlgolohmlcolemabeejnojncnlkjhg"
EXTENSION_URL = f"chrome-extension://{EXTENSION_ID}/popup.html"
STATE_PATH = Path.home() / ".agents" / "state" / "chatgpt-web.json"
WEB_LIMIT_PATTERNS = (
    "usage limit",
    "you've reached",
    "you have reached",
    "message limit",
    "try again after",
    "upgrade your plan",
    "已达到",
    "使用上限",
    "消息上限",
    "额度不足",
)


def run(cmd, timeout=60, check=False):
    try:
        proc = subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "")
        if isinstance(output, bytes):
            output = output.decode(errors="replace")
        return f"TIMEOUT after {timeout}s\n{output}".strip(), 124
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stdout.strip())
    return proc.stdout.strip(), proc.returncode


def doctor_connected():
    out, _ = run(["opencli", "doctor"], timeout=20)
    return "Extension: connected" in out and "Connectivity: connected" in out, out


def close_extension_tabs():
    if platform.system() != "Darwin":
        return
    script = f'''
with timeout of 3 seconds
tell application "Google Chrome"
  repeat with w in windows
    repeat with t in tabs of w
      try
        if (URL of t) starts with "{EXTENSION_URL}" then close t
      end try
    end repeat
  end repeat
end tell
end timeout
'''
    run(["osascript", "-e", script], timeout=5)


def wake_chrome_extension():
    if platform.system() == "Darwin":
        run(["open", "-gja", "Google Chrome", EXTENSION_URL], timeout=10)
        time.sleep(2)


def ensure_connected():
    ok, out = doctor_connected()
    if ok:
        return out

    wake_chrome_extension()
    ok, out = doctor_connected()
    if ok:
        close_extension_tabs()
        return out

    run(["opencli", "daemon", "stop"], timeout=20)
    time.sleep(1)
    wake_chrome_extension()
    ok, out = doctor_connected()
    if ok:
        close_extension_tabs()
        return out

    raise RuntimeError(
        "OpenCLI extension is still disconnected after auto wake/restart.\n"
        "Open chrome://extensions/?id=fgjlgolohmlcolemabeejnojncnlkjhg and click Reload.\n\n"
        + out
    )


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def slug(text):
    base = re.sub(r"\s+", "-", text.strip().lower())[:36]
    base = re.sub(r"[^a-z0-9\u4e00-\u9fff-]+", "", base).strip("-")
    return base or "topic"


def default_state():
    return {"version": 2, "last_topic_id": None, "topics": []}


def load_state():
    if not STATE_PATH.exists():
        return default_state()
    try:
        data = json.loads(STATE_PATH.read_text())
    except Exception:
        return default_state()

    if "topics" in data:
        data.setdefault("version", 2)
        data.setdefault("last_topic_id", None)
        return data

    # Migrate the first rough state file used by the original skill.
    topic = {
        "id": slug(data.get("topic") or "previous"),
        "title": data.get("topic") or "previous",
        "url": data.get("url") or "",
        "summary": data.get("topic") or "",
        "updated_at": data.get("date") or now_iso(),
    }
    return {"version": 2, "last_topic_id": topic["id"], "topics": [topic]}


def save_state(state):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def score_topic(topic, query):
    hay = " ".join(
        [
            topic.get("title", ""),
            topic.get("summary", ""),
            topic.get("url", ""),
        ]
    ).lower()
    q = query.lower().strip()
    if not q:
        return 0
    if q in hay:
        return 100 + len(q)
    tokens = [x for x in re.split(r"[\s,，。/|:：;；]+", q) if x]
    return sum(1 for x in tokens if x in hay)


def select_topic(state, query=None):
    topics = state.get("topics", [])
    if not topics:
        return None
    if query:
        ranked = sorted(((score_topic(t, query), t) for t in topics), reverse=True, key=lambda x: x[0])
        if ranked and ranked[0][0] > 0:
            return ranked[0][1]
    last = state.get("last_topic_id")
    for t in topics:
        if t.get("id") == last:
            return t
    return topics[-1]


def upsert_topic(state, topic):
    topics = [t for t in state.get("topics", []) if t.get("id") != topic["id"]]
    topics.append(topic)
    state["topics"] = topics[-50:]
    state["last_topic_id"] = topic["id"]
    save_state(state)


def list_topics():
    state = load_state()
    rows = []
    for topic in state.get("topics", []):
        mark = "*" if topic.get("id") == state.get("last_topic_id") else " "
        rows.append(f"{mark} {topic.get('title','(untitled)')} | {topic.get('url','')} | {topic.get('updated_at','')}")
    return "\n".join(rows) if rows else "No saved ChatGPT web topics."


def shell_quote(text):
    return shlex.quote(text)


def open_topic_url(url):
    target = url or "https://chatgpt.com/new"
    out, code = run(["opencli", "browser", "open", target], timeout=45)
    if code != 0:
        raise RuntimeError(out)
    time.sleep(3)


def wait_until_done(timeout=120):
    # Give ChatGPT a moment to start streaming before checking for stop buttons.
    time.sleep(8)
    js = (
        "Array.from(document.querySelectorAll('button')).some(b => "
        "/Stop generating|停止生成|Stop streaming|停止/.test("
        "(b.getAttribute('aria-label') || b.textContent || '')))"
    )
    deadline = time.time() + timeout
    while time.time() < deadline:
        out, _ = run(["opencli", "browser", "eval", js], timeout=20)
        if "true" not in out.lower():
            return
        time.sleep(5)


def newest_assistant_text():
    js = r"""
(() => {
  const nodes = Array.from(document.querySelectorAll('[data-message-author-role="assistant"]'));
  const texts = nodes.map(n => n.innerText || n.textContent || '').map(s => s.trim()).filter(Boolean);
  return texts.length ? texts[texts.length - 1] : '';
})()
"""
    out, _ = run(["opencli", "browser", "eval", js], timeout=30)
    text = out.strip()
    # OpenCLI may wrap strings in JSON-ish envelopes depending on version; keep a safe fallback.
    for prefix in ("Result:", "result:"):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        try:
            text = json.loads(text)
        except Exception:
            text = text[1:-1]
    if text:
        return text
    out, _ = run(["opencli", "browser", "extract", "--selector", "main", "--chunk-size", "12000"], timeout=45)
    return out.strip()


def current_url():
    out, _ = run(["opencli", "browser", "get", "url"], timeout=20)
    match = re.search(r"https://chatgpt\.com/[^\s\"']+", out)
    return match.group(0) if match else out.strip()


def conversation_id(url):
    match = re.search(r"https://chatgpt\.com/(?:c/|g/[^/]+/c/)([^/?#\s]+)", url or "")
    return match.group(1) if match else None


def visible_topics():
    ensure_connected()
    open_topic_url("https://chatgpt.com/")
    js = r'''JSON.stringify(Array.from(document.querySelectorAll('a[href*="/c/"]'))
      .map(a => ({url: a.href, title: (a.innerText || a.textContent || '').trim()}))
      .filter(t => t.url && t.title))'''
    try:
        out, code = run(["opencli", "browser", "eval", js], timeout=30)
        if code != 0:
            raise RuntimeError(out)
        rows, _ = json.JSONDecoder().raw_decode(out.lstrip())
        topics = []
        for row in rows:
            cid = conversation_id(row.get("url"))
            if not cid:
                continue
            topics.append({
                "id": f"chatgpt-{cid}",
                "title": row.get("title") or cid,
                "url": row["url"],
                "summary": row.get("title") or "",
                "updated_at": now_iso(),
            })
        return topics
    finally:
        run(["opencli", "browser", "close"], timeout=20)


def discover_topics():
    topics = visible_topics()
    if not topics:
        return "No visible ChatGPT web conversations found."
    return "\n".join(f"{t['title']} | {t['url']}" for t in topics)


def select_visible_topic(query):
    topics = visible_topics()
    if not topics:
        raise RuntimeError("No visible ChatGPT web conversations found.")
    ranked = sorted(((score_topic(t, query), t) for t in topics), reverse=True, key=lambda x: x[0])
    if query and ranked[0][0] == 0:
        raise RuntimeError("No visible ChatGPT conversation matches the requested topic.")
    if not query and len(topics) != 1:
        raise RuntimeError("Multiple visible conversations found; specify a topic title or keyword.")
    topic = ranked[0][1] if query else topics[0]
    state = load_state()
    upsert_topic(state, topic)
    return f"Selected: {topic['title']} | {topic['url']}"


def delegated_prompt(task):
    return (
        "你是研究执行端。请完成下述任务中无需操作用户本机的部分，优先自行联网搜索、"
        "查阅多个可靠来源并交叉核验。输出给上游执行代理的精炼报告，包含：核心结论、"
        "关键证据及来源链接、存在的不确定性、需要上游在本机继续执行或验证的事项。"
        "不要要求用户重复提供可自行搜索的信息，也不要声称完成任何你无法实际验证的"
        "本机操作。\n\n任务：\n" + task
    )


def response_likely_limited(answer):
    lowered = answer.lower()
    return any(pattern.lower() in lowered for pattern in WEB_LIMIT_PATTERNS)


def ask(args):
    ensure_connected()
    state = load_state()

    if args.new:
        title = args.title or args.topic or args.prompt[:40]
        topic = {
            "id": f"{slug(title)}-{int(time.time())}",
            "title": title,
            "url": "https://chatgpt.com/new",
            "summary": args.prompt[:180],
            "updated_at": now_iso(),
        }
    else:
        topic = select_topic(state, args.topic)
        if topic is None:
            raise RuntimeError(
                "No saved ChatGPT conversation is selected. "
                "Use `discover` and `select` first, or pass `--new` explicitly."
            )

    prompt = delegated_prompt(args.prompt) if getattr(args, "delegate", False) else args.prompt
    if args.search:
        prompt = "Search the web for: " + prompt

    try:
        open_topic_url(topic.get("url"))
        if not args.new:
            loaded_url = current_url()
            if conversation_id(loaded_url) != conversation_id(topic.get("url")):
                raise RuntimeError(
                    "The selected ChatGPT conversation is unavailable or redirected to the home page. "
                    "No prompt was sent. Use `discover` and `select` to choose an accessible conversation."
                )
        state_out, _ = run(["opencli", "browser", "state"], timeout=30)
        if "#prompt-textarea" not in state_out and "与 ChatGPT 聊天" not in state_out and "Message ChatGPT" not in state_out:
            raise RuntimeError("ChatGPT composer not found. The browser may not be logged in or the page layout changed.")

        out, code = run(["opencli", "browser", "type", "#prompt-textarea", prompt], timeout=45)
        if code != 0:
            raise RuntimeError(out)
        run(["opencli", "browser", "keys", "Enter"], timeout=20, check=True)
        wait_until_done(args.timeout)
        answer = newest_assistant_text()
        url = current_url()

        if url.startswith("https://chatgpt.com/"):
            topic["url"] = url
        if args.title:
            topic["title"] = args.title
        topic["summary"] = (topic.get("summary") or args.prompt)[:180]
        topic["updated_at"] = now_iso()
        upsert_topic(state, topic)

        print(f"TOPIC: {topic.get('title')}")
        print(f"URL: {topic.get('url')}")
        if getattr(args, "delegate", False):
            status = "WEB_LIMIT_POSSIBLE" if response_likely_limited(answer) else "WEB_DELEGATION_COMPLETED"
            print(f"DELEGATION_STATUS: {status}")
        print("\nANSWER:\n" + answer)
    finally:
        if not args.keep_open:
            run(["opencli", "browser", "close"], timeout=20)


def main():
    parser = argparse.ArgumentParser(description="ChatGPT web helper for Codex/Claude skills.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor")
    sub.add_parser("list")
    sub.add_parser("discover")
    select_p = sub.add_parser("select")
    select_p.add_argument("topic", nargs="?", help="Existing visible topic title or keyword.")

    ask_p = sub.add_parser("ask")
    ask_p.add_argument("prompt")
    ask_p.add_argument("--topic", help="Existing topic title, keyword, or rough meaning to continue.")
    ask_p.add_argument("--new", action="store_true", help="Force a new ChatGPT conversation.")
    ask_p.add_argument("--title", help="Title to save for a new or existing topic.")
    ask_p.add_argument("--search", action="store_true", help="Prefix the prompt as a web-search request.")
    ask_p.add_argument("--keep-open", action="store_true", help="Do not close the OpenCLI automation window.")
    ask_p.add_argument("--timeout", type=int, default=120)

    delegate_p = sub.add_parser("delegate")
    delegate_p.add_argument("prompt", help="Research or analysis work to delegate to ChatGPT web.")
    delegate_p.add_argument("--topic", help="Existing selected/saved topic title or keyword to continue.")
    delegate_p.add_argument("--search", action="store_true", help="Prefix the delegated task as a web-search request.")
    delegate_p.add_argument("--keep-open", action="store_true", help="Do not close the OpenCLI automation window.")
    delegate_p.add_argument("--timeout", type=int, default=180)
    delegate_p.add_argument("--dry-run", action="store_true", help="Print the delegation prompt without sending it.")
    delegate_p.set_defaults(new=False, title=None, delegate=True)

    args = parser.parse_args()
    if args.cmd == "doctor":
        print(ensure_connected())
        return
    if args.cmd == "list":
        print(list_topics())
        return
    if args.cmd == "discover":
        print(discover_topics())
        return
    if args.cmd == "select":
        print(select_visible_topic(args.topic))
        return
    if args.cmd == "ask":
        ask(args)
        return
    if args.cmd == "delegate":
        if args.dry_run:
            print(delegated_prompt(args.prompt))
            return
        ask(args)


if __name__ == "__main__":
    main()
