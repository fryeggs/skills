#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import platform
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

EXTENSION_ID = "fgjlgolohmlcolemabeejnojncnlkjhg"
EXTENSION_URL = f"chrome-extension://{EXTENSION_ID}/popup.html"
STATE_PATH = Path.home() / ".agents" / "state" / "chatgpt-web.json"
LOCK_PATH = Path.home() / ".agents" / "state" / "chatgpt-web.lock"
METRICS_PATH = Path.home() / ".agents" / "state" / "chatgpt-web-metrics.jsonl"
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
RETURN_MODES = ("receipt", "capsule", "full")
DEFAULT_RETURN_MODE = "capsule"
DEFAULT_MAX_CHARS = 2000
CAPSULE_START = "<codex_capsule>"
CAPSULE_END = "</codex_capsule>"
COMPOSER_SELECTORS = (
    "#prompt-textarea",
    'textarea[data-testid="prompt-textarea"]',
    '[data-testid="prompt-textarea"][contenteditable="true"]',
    'textarea[aria-label*="ChatGPT"]',
    '[contenteditable="true"][role="textbox"][aria-label*="ChatGPT"]',
)
SEND_BUTTON_SELECTOR = 'button[data-testid="send-button"]'


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


def pid_is_alive(pid):
    """Check if a process with the given positive PID is alive.

    PID 0 and negative values are not valid process identifiers and
    are never considered alive.
    """
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def parse_opencli_target_id(output):
    """Parse target page ID from OpenCLI browser-open JSON output.

    OpenCLI merges stderr into stdout, so the output may contain
    surrounding informational/update text.  Scan for the first valid
    JSON object that carries a non-empty *string* ``page`` field.
    Reject numeric or empty target IDs as malformed.
    Returns the target ID string or None.
    """
    if not output or not output.strip():
        return None
    text = output.strip()
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(text):
        try:
            obj, end = decoder.raw_decode(text, idx)
        except json.JSONDecodeError:
            idx += 1
            continue
        if isinstance(obj, dict) and "page" in obj:
            page = obj["page"]
            if isinstance(page, str) and page.strip():
                return page.strip()
        idx = end
    return None


class TaskLock:
    """Atomic single-task lock to prevent concurrent automation window usage."""

    def __init__(self, run_id, cmd_type="unknown"):
        self.run_id = run_id
        self.cmd_type = cmd_type
        self.lock_file = LOCK_PATH
        self.acquired = False

    def acquire(self):
        """Try to acquire the lock. Returns True if successful, False if locked."""
        try:
            # Ensure parent directory exists for first run
            self.lock_file.parent.mkdir(parents=True, exist_ok=True)
            # Atomic create - fails if file exists
            fd = os.open(str(self.lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            lock_data = {
                "run_id": self.run_id,
                "pid": os.getpid(),
                "started_at": now_iso(),
                "cmd_type": self.cmd_type,
            }
            os.write(fd, json.dumps(lock_data).encode())
            os.close(fd)
            self.acquired = True
            return True
        except FileExistsError:
            # Check if lock is stale: older than 10 minutes AND PID is dead
            try:
                lock_data = json.loads(self.lock_file.read_text())
                lock_pid = lock_data.get("pid")
                started = dt.datetime.fromisoformat(lock_data.get("started_at", "2000-01-01"))
                age_seconds = (dt.datetime.now() - started).total_seconds()
                if age_seconds > 600:
                    # PID must be a positive integer to be considered live
                    if lock_pid is None:
                        # No PID field: malformed, recover
                        try:
                            self.lock_file.unlink()
                        except FileNotFoundError:
                            pass
                        return self.acquire()
                    try:
                        lock_pid_int = int(lock_pid)
                    except (ValueError, TypeError):
                        # Non-integer PID: malformed, recover
                        try:
                            self.lock_file.unlink()
                        except FileNotFoundError:
                            pass
                        return self.acquire()
                    if lock_pid_int <= 0 or not pid_is_alive(lock_pid_int):
                        # PID 0/negative is malformed; dead PID is stale
                        try:
                            self.lock_file.unlink()
                        except FileNotFoundError:
                            pass
                        return self.acquire()
            except (json.JSONDecodeError, ValueError, TypeError, OSError):
                # Malformed lock file: recover only if truly unreadable
                pass
            return False

    def release(self):
        """Release the lock if we hold it."""
        if self.acquired:
            try:
                self.lock_file.unlink()
            except FileNotFoundError:
                pass
            self.acquired = False

    def __enter__(self):
        if not self.acquire():
            raise RuntimeError(
                "Another ChatGPT web task is already running. "
                "Wait for it to finish or check ~/.agents/state/chatgpt-web.lock"
            )
        return self

    def __exit__(self, *args):
        self.release()


def record_metrics(run_id, return_mode, success, response_chars=0, printed_chars=0,
                   minimize_ok=False, cleanup_ok=False, kept_open=False):
    """Record non-sensitive metadata for estimating context savings."""
    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    estimated_avoided = max(0, response_chars - printed_chars)
    # Rough estimate: ~4 chars per token
    estimated_tokens_avoided = estimated_avoided // 4
    entry = {
        "ts": now_iso(),
        "run_id": run_id,
        "return_mode": return_mode,
        "success": success,
        "response_chars": response_chars,
        "printed_chars": printed_chars,
        "estimated_avoided_chars": estimated_avoided,
        "estimated_avoided_tokens": estimated_tokens_avoided,
        "minimize_ok": minimize_ok,
        "cleanup_ok": cleanup_ok,
        "kept_open": kept_open,
    }
    with open(str(METRICS_PATH), "a") as f:
        f.write(json.dumps(entry) + "\n")


def extract_capsule(text):
    """Extract <codex_capsule> JSON from response text.
    Returns (parsed_dict, raw_json_str) or (None, None) if not found/invalid."""
    start_idx = text.find(CAPSULE_START)
    end_idx = text.find(CAPSULE_END)
    if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
        return None, None
    raw = text[start_idx + len(CAPSULE_START):end_idx].strip()
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed, raw
    except json.JSONDecodeError:
        pass
    return None, None


def format_capsule_output(capsule_data, url, max_chars=DEFAULT_MAX_CHARS, delegation_status=None):
    """Format capsule data as a single valid JSON envelope, respecting max_chars.

    The entire printed payload is ONE valid JSON object parsable by
    ``json.loads(output)``.  It contains at minimum ``status`` and ``url``.
    When the full capsule fits, it is included under the ``capsule`` key;
    otherwise a reduced capsule with truncation metadata is emitted.
    If *delegation_status* is provided, it is included in the envelope so
    the final printed JSON respects *max_chars* as a whole.
    If even the minimal status/url envelope exceeds *max_chars*, raise
    ``ValueError`` before printing anything.
    """
    envelope = {
        "status": "ok",
        "url": url,
        "capsule": capsule_data,
        "truncated": False,
    }
    if delegation_status is not None:
        envelope["delegation_status"] = delegation_status
    output = json.dumps(envelope, ensure_ascii=False, indent=2)
    if len(output) <= max_chars:
        return output
    # Build a reduced capsule with truncation metadata
    reduced = {
        "conclusion": capsule_data.get("conclusion", "")[:200],
        "evidence": capsule_data.get("evidence", [])[:2],
        "truncated_original_fields": sorted(capsule_data.keys()),
    }
    envelope["capsule"] = reduced
    envelope["truncated"] = True
    output = json.dumps(envelope, ensure_ascii=False, indent=2)
    if len(output) <= max_chars:
        return output
    # Even reduced form exceeds limit: try status-only envelope
    minimal = {"status": "ok", "url": url, "truncated": True, "capsule": None}
    if delegation_status is not None:
        minimal["delegation_status"] = delegation_status
    minimal_json = json.dumps(minimal, ensure_ascii=False)
    if len(minimal_json) > max_chars:
        raise ValueError(
            f"capsule envelope ({len(minimal_json)} chars) exceeds max_chars ({max_chars})"
        )
    return minimal_json


def format_extraction_failure_output(url, topic_title, max_chars=DEFAULT_MAX_CHARS, delegation_status=None):
    """Format capsule extraction failure as valid JSON, respecting max_chars.

    Raises ``ValueError`` if the mandatory minimal envelope cannot fit.
    """
    envelope = {
        "status": "extraction_failed",
        "url": url,
        "topic": topic_title,
        "hint": "Use --return-mode full to get the complete answer.",
    }
    if delegation_status is not None:
        envelope["delegation_status"] = delegation_status
    output = json.dumps(envelope, ensure_ascii=False, indent=2)
    if len(output) <= max_chars:
        return output
    # Try compact without hint
    minimal = {"status": "extraction_failed", "url": url}
    if delegation_status is not None:
        minimal["delegation_status"] = delegation_status
    minimal_json = json.dumps(minimal, ensure_ascii=False)
    if len(minimal_json) > max_chars:
        raise ValueError(
            f"extraction failure envelope ({len(minimal_json)} chars) exceeds max_chars ({max_chars})"
        )
    return minimal_json


def format_receipt_output(title, url, status="COMPLETED"):
    """Format receipt-only output."""
    return f"STATUS: {status}\nTOPIC: {title}\nURL: {url}"


def augment_prompt_for_capsule(prompt):
    """Append capsule protocol instruction to prompt for capsule mode."""
    return prompt + """

<codex_output_protocol>
When you finish your response, output the following JSON block exactly as shown, with your actual findings filled in:

<codex_capsule>
{"conclusion":"<your main conclusion in 1-3 sentences>","evidence":[{"claim":"<key claim>","source":"<source or reasoning>"}],"uncertainties":["<what you are unsure about>"],"actions_for_codex":["<what the upstream agent should do next>"]}
</codex_capsule>

Put all your detailed analysis before the capsule. The capsule should be a concise structured summary.
</codex_output_protocol>"""


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


class OwnedWindowManager:
    """Manages Chrome automation tab with target-based identification.

    Uses a unique ChatGPT fragment marker URL and isolated OpenCLI session to
    establish ownership of a dedicated background browser window. All
    subsequent browser operations target that retained tab ID in the same
    session. Cleanup releases only the owned session window.

    Safety: Only operates on tabs that can be uniquely identified as belonging
    to this run via a marker URL or target ID. Aborts if uniqueness cannot be
    proven before sending the user prompt.
    """

    def __init__(self, run_id):
        self.run_id = run_id
        session_suffix = re.sub(r"[^A-Za-z0-9]", "", run_id)
        self.session = f"chatgptweb{session_suffix}"
        self.marker_url = f"https://chatgpt.com/#chatgpt-web-{run_id}"
        self.target_id = None
        self.is_darwin = platform.system() == "Darwin"

    def open_marker(self):
        """Create an isolated background automation window with marker URL.

        OpenCLI v1.8 requires an explicit session and accepts only HTTP(S)
        URLs. ``--window background open`` produced a single-tab dedicated
        window in live acceptance testing. Returns its target ID or None.
        """
        out, code = run(
            [
                "opencli", "browser", self.session, "--window", "background",
                "open", self.marker_url,
            ],
            timeout=30,
        )
        if code != 0:
            return None
        self.target_id = parse_opencli_target_id(out)
        return self.target_id

    def navigate_to_topic(self, topic_url):
        """Navigate the owned target to the topic URL.

        Returns True on success, False if target is not set or navigation fails.
        """
        if not self.target_id:
            return False
        out, code = run(
            ["opencli", "browser", self.session, "open", "--tab", self.target_id, topic_url],
            timeout=45,
        )
        if code != 0:
            return False
        time.sleep(3)
        return True

    def identify_and_minimize(self):
        """Identify the owned Chrome window by marker URL and minimize it.

        Only minimizes if the marker tab is the sole tab in its window.
        If the window contains other tabs, returns False to signal the caller
        should abort (to avoid minimizing a shared user window).

        Returns True if successfully identified and minimized (or non-macOS).
        Returns False if unable to uniquely identify or window is shared.
        """
        if not self.is_darwin:
            return True
        script = '''tell application "Google Chrome"
  set matchedWindows to ""
  set windowIndex to 0
  repeat with w in windows
    set windowIndex to windowIndex + 1
    set tabCount to count of tabs of w
    repeat with t in tabs of w
      try
        if (URL of t) starts with "https://chatgpt.com/#chatgpt-web-" then
          set matchedWindows to matchedWindows & windowIndex & ":" & tabCount & ":" & (URL of t) & "\\n"
        end if
      end try
    end repeat
  end repeat
  return matchedWindows
end tell'''
        out, code = run(["osascript", "-e", script], timeout=10)
        if code != 0:
            return False
        matches = []
        for line in out.strip().split("\n"):
            if ":" in line:
                parts = line.split(":", 2)
                try:
                    idx = int(parts[0].strip())
                    tab_count = int(parts[1].strip())
                    url = parts[2].strip()
                    matches.append((idx, tab_count, url))
                except ValueError:
                    continue
        owned = [(idx, tab_count, url) for idx, tab_count, url in matches if self.run_id in url]
        if len(owned) != 1:
            return False
        owned_window_index = owned[0][0]
        tab_count = owned[0][1]
        # Only minimize if the owned tab is the sole tab in the window
        if tab_count > 1:
            return False
        minimize_script = f'''tell application "Google Chrome"
  set minimized of window {owned_window_index} to true
end tell'''
        _, code = run(["osascript", "-e", minimize_script], timeout=5)
        return code == 0

    def close_owned_window(self):
        """Release only this run's uniquely named OpenCLI browser session."""
        if not self.target_id:
            return False
        try:
            _, code = run(
                ["opencli", "browser", self.session, "close"],
                timeout=15,
            )
            return code == 0
        except Exception:
            return False

    def cleanup(self):
        """Best-effort cleanup: release the owned session window if created."""
        try:
            return self.close_owned_window()
        except Exception:
            return False


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


def locked_connection_check():
    """Check/wake OpenCLI without racing another browser automation task."""
    run_id = str(uuid.uuid4())[:8]
    with TaskLock(run_id, cmd_type="doctor"):
        return ensure_connected()


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


def wait_until_done(session, timeout=120, target_id=None):
    time.sleep(8)
    js = (
        "Array.from(document.querySelectorAll('button')).some(b => "
        "/Stop generating|停止生成|Stop streaming|停止/.test("
        "(b.getAttribute('aria-label') || b.textContent || '')))"
    )
    deadline = time.time() + timeout
    tab_args = ["--tab", target_id] if target_id else []
    while time.time() < deadline:
        out, _ = run(["opencli", "browser", session, "eval"] + tab_args + [js], timeout=20)
        if "true" not in out.lower():
            return
        time.sleep(5)


def newest_assistant_text(session, target_id=None):
    js = r"""
(() => {
  const nodes = Array.from(document.querySelectorAll('[data-message-author-role="assistant"]'));
  const texts = nodes.map(n => n.innerText || n.textContent || '').map(s => s.trim()).filter(Boolean);
  return texts.length ? texts[texts.length - 1] : '';
})()
"""
    tab_args = ["--tab", target_id] if target_id else []
    out, _ = run(["opencli", "browser", session, "eval"] + tab_args + [js], timeout=30)
    text = out.strip()
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
    out, _ = run(["opencli", "browser", session, "extract"] + tab_args + ["--selector", "main", "--chunk-size", "12000"], timeout=45)
    return out.strip()


def current_url(session, target_id=None):
    tab_args = ["--tab", target_id] if target_id else []
    out, _ = run(["opencli", "browser", session, "get", "url"] + tab_args, timeout=20)
    match = re.search(r"https://chatgpt\.com/[^\s\"']+", out)
    return match.group(0) if match else out.strip()


def find_composer_selector(session, target_id=None):
    """Return a usable ChatGPT composer selector found directly in the DOM."""
    selectors = json.dumps(COMPOSER_SELECTORS)
    js = f"""(() => {{
  const selectors = {selectors};
  const index = selectors.findIndex(selector => {{
    const element = document.querySelector(selector);
    return element && !element.disabled && element.getAttribute('aria-disabled') !== 'true';
  }});
  return index >= 0 ? 'CHATGPT_WEB_COMPOSER:' + index : 'CHATGPT_WEB_COMPOSER:none';
}})()"""
    tab_args = ["--tab", target_id] if target_id else []
    out, code = run(["opencli", "browser", session, "eval"] + tab_args + [js], timeout=30)
    if code != 0:
        return None
    match = re.search(r"CHATGPT_WEB_COMPOSER:(\d+)", out)
    if not match:
        return None
    index = int(match.group(1))
    return COMPOSER_SELECTORS[index] if index < len(COMPOSER_SELECTORS) else None


def submit_prompt(session, target_id=None):
    """Submit the prepared prompt through ChatGPT's owned-tab send button."""
    selector = json.dumps(SEND_BUTTON_SELECTOR)
    js = f"""(() => {{
  const button = document.querySelector({selector});
  if (!button || button.disabled || button.getAttribute('aria-disabled') === 'true') {{
    return 'CHATGPT_WEB_SUBMIT:unavailable';
  }}
  button.click();
  return 'CHATGPT_WEB_SUBMIT:clicked';
}})()"""
    tab_args = ["--tab", target_id] if target_id else []
    out, code = run(["opencli", "browser", session, "eval"] + tab_args + [js], timeout=20)
    return code == 0 and "CHATGPT_WEB_SUBMIT:clicked" in out


def conversation_id(url):
    match = re.search(r"https://chatgpt\.com/(?:c/|g/[^/]+/c/)([^/?#\s]+)", url or "")
    return match.group(1) if match else None


def visible_topics():
    run_id = str(uuid.uuid4())[:8]
    with TaskLock(run_id, cmd_type="discover"):
        ensure_connected()
        window_mgr = OwnedWindowManager(run_id)
        target_id = window_mgr.open_marker()
        if not target_id:
            raise RuntimeError(
                "Failed to open automation tab for discover. "
                "OpenCLI may be disconnected."
            )
        try:
            if window_mgr.is_darwin:
                if not window_mgr.identify_and_minimize():
                    raise RuntimeError(
                        "Could not safely minimize the owned automation window for discover. "
                        "Aborting to avoid operating on user windows."
                    )
            if not window_mgr.navigate_to_topic("https://chatgpt.com/"):
                raise RuntimeError("Failed to navigate to ChatGPT for discover.")
            js = r'''JSON.stringify(Array.from(document.querySelectorAll('a[href*="/c/"]'))
              .map(a => ({url: a.href, title: (a.innerText || a.textContent || '').trim()}))
              .filter(t => t.url && t.title))'''
            out, code = run(
                ["opencli", "browser", window_mgr.session, "eval", "--tab", target_id, js], timeout=30
            )
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
            window_mgr.cleanup()


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
    run_id = str(uuid.uuid4())[:8]
    return_mode = getattr(args, "return_mode", DEFAULT_RETURN_MODE)
    max_chars = getattr(args, "max_chars", DEFAULT_MAX_CHARS)
    is_delegate = getattr(args, "delegate", False)
    keep_open = getattr(args, "keep_open", False)

    minimize_ok = False
    cleanup_ok = False
    response_chars = 0
    printed_chars = 0
    success = False
    already_cleaned = False
    window_mgr = OwnedWindowManager(run_id)

    with TaskLock(run_id, cmd_type="delegate" if is_delegate else "ask"):
        try:
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

            prompt = delegated_prompt(args.prompt) if is_delegate else args.prompt
            if args.search:
                prompt = "Search the web for: " + prompt

            if return_mode == "capsule":
                prompt = augment_prompt_for_capsule(prompt)

            # Open a unique fragment marker in an isolated browser session.
            target_id = window_mgr.open_marker()
            if not target_id:
                raise RuntimeError(
                    "Failed to open automation tab. OpenCLI may be disconnected."
                )

            # macOS: identify marker window and minimize
            if window_mgr.is_darwin:
                if not window_mgr.identify_and_minimize():
                    cleanup_ok = window_mgr.cleanup()
                    already_cleaned = True
                    raise RuntimeError(
                        "Could not safely minimize the owned automation window. "
                        "The owned tab may share a window with other tabs, or "
                        "uniqueness could not be proven. "
                        "Aborting to avoid operating on user windows."
                    )
                minimize_ok = True

            # Navigate owned target to topic URL
            if not window_mgr.navigate_to_topic(topic.get("url")):
                raise RuntimeError(
                    "Failed to navigate to topic URL. "
                    "The automation target may have been lost."
                )

            if not args.new:
                loaded_url = current_url(window_mgr.session, target_id=target_id)
                if conversation_id(loaded_url) != conversation_id(topic.get("url")):
                    raise RuntimeError(
                        "The selected ChatGPT conversation is unavailable or redirected to the home page. "
                        "No prompt was sent. Use `discover` and `select` to choose an accessible conversation."
                    )

            composer_selector = find_composer_selector(window_mgr.session, target_id=target_id)
            if not composer_selector:
                raise RuntimeError("ChatGPT composer not found in the page DOM. The browser may not be logged in or the page layout changed.")

            out, code = run(
                ["opencli", "browser", window_mgr.session, "type", "--tab", target_id, composer_selector, prompt],
                timeout=45,
            )
            if code != 0:
                raise RuntimeError(out)
            if not submit_prompt(window_mgr.session, target_id=target_id):
                raise RuntimeError("ChatGPT send button could not be activated in the owned automation tab.")
            wait_until_done(window_mgr.session, args.timeout, target_id=target_id)
            answer = newest_assistant_text(window_mgr.session, target_id=target_id)
            url = current_url(window_mgr.session, target_id=target_id)

            response_chars = len(answer)

            if url.startswith("https://chatgpt.com/"):
                topic["url"] = url
            if args.title:
                topic["title"] = args.title
            topic["summary"] = (topic.get("summary") or args.prompt)[:180]
            topic["updated_at"] = now_iso()
            upsert_topic(state, topic)

            if return_mode == "receipt":
                status = "WEB_LIMIT_POSSIBLE" if response_likely_limited(answer) else "COMPLETED"
                output = format_receipt_output(topic.get("title"), topic.get("url"), status)
                if is_delegate:
                    output = f"DELEGATION_STATUS: {status}\n{output}"
                print(output)
                printed_chars = len(output)
                success = True

            elif return_mode == "capsule":
                capsule_data, raw_json = extract_capsule(answer)
                delegation_status_val = "COMPLETED" if is_delegate else None
                if capsule_data is not None:
                    output = format_capsule_output(
                        capsule_data, topic.get("url"), max_chars,
                        delegation_status=delegation_status_val,
                    )
                    success = True
                    print(output)
                    printed_chars = len(output)
                else:
                    delegation_status_fail = "CAPSULE_FAILED" if is_delegate else None
                    output = format_extraction_failure_output(
                        topic.get("url"), topic.get("title"), max_chars,
                        delegation_status=delegation_status_fail,
                    )
                    print(output)
                    printed_chars = len(output)

            else:
                if is_delegate:
                    status = "WEB_LIMIT_POSSIBLE" if response_likely_limited(answer) else "WEB_DELEGATION_COMPLETED"
                    print(f"DELEGATION_STATUS: {status}")
                print(f"TOPIC: {topic.get('title')}")
                print(f"URL: {topic.get('url')}")
                print("\nANSWER:\n" + answer)
                printed_chars = len(answer) + len(topic.get("title", "")) + len(topic.get("url", "")) + 20
                success = True

        finally:
            try:
                if not keep_open and not already_cleaned:
                    cleanup_ok = window_mgr.cleanup()
            except Exception:
                cleanup_ok = False
            try:
                record_metrics(
                    run_id=run_id,
                    return_mode=return_mode,
                    success=success,
                    response_chars=response_chars,
                    printed_chars=printed_chars,
                    minimize_ok=minimize_ok,
                    cleanup_ok=cleanup_ok,
                    kept_open=keep_open and not already_cleaned,
                )
            except Exception:
                pass


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
    ask_p.add_argument("--return-mode", choices=RETURN_MODES, default=DEFAULT_RETURN_MODE,
                       help="Return mode: receipt (status+URL only), capsule (structured extract), full (complete answer). Default: capsule")
    ask_p.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS,
                       help="Maximum characters for capsule output. Default: 2000")

    delegate_p = sub.add_parser("delegate")
    delegate_p.add_argument("prompt", help="Research or analysis work to delegate to ChatGPT web.")
    delegate_p.add_argument("--topic", help="Existing selected/saved topic title or keyword to continue.")
    delegate_p.add_argument("--search", action="store_true", help="Prefix the delegated task as a web-search request.")
    delegate_p.add_argument("--keep-open", action="store_true", help="Do not close the OpenCLI automation window.")
    delegate_p.add_argument("--timeout", type=int, default=180)
    delegate_p.add_argument("--dry-run", action="store_true", help="Print the delegation prompt without sending it.")
    delegate_p.add_argument("--return-mode", choices=RETURN_MODES, default=DEFAULT_RETURN_MODE,
                           help="Return mode: receipt (status+URL only), capsule (structured extract), full (complete answer). Default: capsule")
    delegate_p.add_argument("--max-chars", type=int, default=DEFAULT_MAX_CHARS,
                           help="Maximum characters for capsule output. Default: 2000")
    delegate_p.set_defaults(new=False, title=None, delegate=True)

    args = parser.parse_args()
    if args.cmd == "doctor":
        print(locked_connection_check())
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
