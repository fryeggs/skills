#!/usr/bin/env python3
"""Unit tests for chatgpt_web.py - offline tests with mocked subprocess/AppleScript calls."""
import argparse
import datetime as dt
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import chatgpt_web


class TestParseOpencliTargetId(unittest.TestCase):
    """Test parsing target ID from OpenCLI browser-open JSON output."""

    def test_parse_valid_json_with_page_string(self):
        output = '{"page":"tab-1","url":"https://example.com"}'
        self.assertEqual(chatgpt_web.parse_opencli_target_id(output), "tab-1")

    def test_parse_valid_json_with_page_numeric_rejected(self):
        """Numeric page values are rejected as malformed."""
        output = '{"page": 3, "url": "about:blank"}'
        self.assertIsNone(chatgpt_web.parse_opencli_target_id(output))

    def test_parse_valid_json_with_page_empty_string_rejected(self):
        """Empty string page values are rejected."""
        output = '{"page": "", "url": "about:blank"}'
        self.assertIsNone(chatgpt_web.parse_opencli_target_id(output))

    def test_parse_valid_json_with_page_whitespace_only_rejected(self):
        """Whitespace-only page values are rejected."""
        output = '{"page": "   ", "url": "about:blank"}'
        self.assertIsNone(chatgpt_web.parse_opencli_target_id(output))

    def test_parse_no_page_field(self):
        output = '{"url":"https://example.com","title":"Test"}'
        self.assertIsNone(chatgpt_web.parse_opencli_target_id(output))

    def test_parse_non_dict_json(self):
        output = '["page", "tab-1"]'
        self.assertIsNone(chatgpt_web.parse_opencli_target_id(output))

    def test_parse_invalid_json(self):
        output = 'not json at all'
        self.assertIsNone(chatgpt_web.parse_opencli_target_id(output))

    def test_parse_empty_string(self):
        self.assertIsNone(chatgpt_web.parse_opencli_target_id(""))

    def test_parse_realistic_opencli_output(self):
        output = '{"page":"tab-1","url":"about:blank#chatgpt-web-a1b2c3d4","title":""}'
        self.assertEqual(chatgpt_web.parse_opencli_target_id(output), "tab-1")

    def test_parse_with_prefix_notice_text(self):
        """JSON object embedded after informational text is found."""
        output = 'OpenCLI v2.3.0\nConnecting to browser...\n{"page":"tab-5","url":"about:blank#chatgpt-web-xyz"}\nDone.'
        self.assertEqual(chatgpt_web.parse_opencli_target_id(output), "tab-5")

    def test_parse_with_suffix_notice_text(self):
        """JSON object followed by trailing text is found."""
        output = '{"page":"tab-2","url":"about:blank"}\nTab created successfully.'
        self.assertEqual(chatgpt_web.parse_opencli_target_id(output), "tab-2")

    def test_parse_with_prefix_and_suffix(self):
        """JSON object surrounded by notice text is found."""
        output = 'INFO: creating tab\n{"page":"my-target-id","url":"about:blank"}\nOK\n'
        self.assertEqual(chatgpt_web.parse_opencli_target_id(output), "my-target-id")

    def test_parse_page_numeric_zero_rejected(self):
        output = '{"page": 0}'
        self.assertIsNone(chatgpt_web.parse_opencli_target_id(output))

    def test_parse_page_negative_rejected(self):
        output = '{"page": -1}'
        self.assertIsNone(chatgpt_web.parse_opencli_target_id(output))

    def test_parse_page_float_rejected(self):
        output = '{"page": 1.5}'
        self.assertIsNone(chatgpt_web.parse_opencli_target_id(output))

    def test_parse_page_none_rejected(self):
        output = '{"page": null}'
        self.assertIsNone(chatgpt_web.parse_opencli_target_id(output))

    def test_parse_page_bool_rejected(self):
        output = '{"page": true}'
        self.assertIsNone(chatgpt_web.parse_opencli_target_id(output))


class TestPidIsAlive(unittest.TestCase):
    """Test PID liveness check."""

    def test_current_pid_is_alive(self):
        self.assertTrue(chatgpt_web.pid_is_alive(os.getpid()))

    def test_nonexistent_pid_is_not_alive(self):
        self.assertFalse(chatgpt_web.pid_is_alive(999999))

    def test_pid_zero_is_malformed_not_alive(self):
        """PID 0 is not a valid positive PID; should not be considered alive."""
        self.assertFalse(chatgpt_web.pid_is_alive(0))


class TestCapsuleExtraction(unittest.TestCase):
    """Test capsule extraction and parsing."""

    def test_extract_valid_capsule(self):
        text = """Here is my analysis.

<codex_capsule>
{"conclusion":"The main finding is X","evidence":[{"claim":"Claim 1","source":"Source A"}],"uncertainties":["Unknown Y"],"actions_for_codex":["Verify Z"]}
</codex_capsule>"""
        capsule, raw = chatgpt_web.extract_capsule(text)
        self.assertIsNotNone(capsule)
        self.assertEqual(capsule["conclusion"], "The main finding is X")
        self.assertEqual(len(capsule["evidence"]), 1)
        self.assertEqual(capsule["evidence"][0]["claim"], "Claim 1")

    def test_extract_capsule_missing(self):
        text = "Just a regular response without any capsule."
        capsule, raw = chatgpt_web.extract_capsule(text)
        self.assertIsNone(capsule)
        self.assertIsNone(raw)

    def test_extract_capsule_invalid_json(self):
        text = """<codex_capsule>
{invalid json here}
</codex_capsule>"""
        capsule, raw = chatgpt_web.extract_capsule(text)
        self.assertIsNone(capsule)

    def test_extract_capsule_not_dict(self):
        text = """<codex_capsule>
["this", "is", "a", "list"]
</codex_capsule>"""
        capsule, raw = chatgpt_web.extract_capsule(text)
        self.assertIsNone(capsule)

    def test_extract_capsule_missing_end_tag(self):
        text = """<codex_capsule>
{"conclusion":"test"}"""
        capsule, raw = chatgpt_web.extract_capsule(text)
        self.assertIsNone(capsule)


class TestCapsuleFormatting(unittest.TestCase):
    """Test capsule output formatting and length limiting."""

    def test_format_within_limit_is_valid_json_envelope(self):
        capsule = {"conclusion": "Short conclusion", "evidence": [], "uncertainties": [], "actions_for_codex": []}
        output = chatgpt_web.format_capsule_output(capsule, "https://chatgpt.com/c/test", max_chars=500)
        self.assertLessEqual(len(output), 500)
        parsed = json.loads(output)
        self.assertEqual(parsed["status"], "ok")
        self.assertEqual(parsed["url"], "https://chatgpt.com/c/test")
        self.assertFalse(parsed["truncated"])
        self.assertEqual(parsed["capsule"]["conclusion"], "Short conclusion")

    def test_format_truncation_produces_valid_json_envelope(self):
        capsule = {"conclusion": "A" * 3000, "evidence": [{"claim": "x", "source": "y"}],
                    "uncertainties": ["u"], "actions_for_codex": ["a"]}
        output = chatgpt_web.format_capsule_output(capsule, "https://chatgpt.com/c/test", max_chars=2000)
        self.assertLessEqual(len(output), 2000)
        parsed = json.loads(output)
        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed["status"], "ok")
        self.assertEqual(parsed["url"], "https://chatgpt.com/c/test")
        self.assertTrue(parsed["truncated"])

    def test_format_truncation_has_url_and_truncated_flag(self):
        capsule = {"conclusion": "B" * 3000, "evidence": [], "uncertainties": [], "actions_for_codex": []}
        output = chatgpt_web.format_capsule_output(capsule, "https://chatgpt.com/c/abc", max_chars=2000)
        parsed = json.loads(output)
        self.assertTrue(parsed.get("truncated"))
        self.assertEqual(parsed.get("url"), "https://chatgpt.com/c/abc")

    def test_format_truncation_includes_truncated_original_fields(self):
        capsule = {"conclusion": "C" * 3000, "evidence": [], "uncertainties": ["u"], "actions_for_codex": []}
        output = chatgpt_web.format_capsule_output(capsule, "https://chatgpt.com/c/test", max_chars=2000)
        parsed = json.loads(output)
        self.assertIn("truncated_original_fields", parsed["capsule"])
        self.assertIn("conclusion", parsed["capsule"]["truncated_original_fields"])
        self.assertIn("uncertainties", parsed["capsule"]["truncated_original_fields"])

    def test_format_very_small_max_chars_raises_error(self):
        """When even the minimal envelope cannot fit, raise ValueError."""
        capsule = {"conclusion": "D" * 1000, "evidence": [], "uncertainties": [], "actions_for_codex": []}
        with self.assertRaises(ValueError):
            chatgpt_web.format_capsule_output(capsule, "https://chatgpt.com/c/test", max_chars=10)

    def test_format_output_is_always_single_valid_json(self):
        """All truncation levels must produce a single parseable JSON object."""
        capsule = {"conclusion": "E" * 500, "evidence": [{"claim": "c", "source": "s"}] * 10,
                    "uncertainties": ["u"] * 5, "actions_for_codex": ["a"] * 5}
        for max_chars in [200, 500, 1000, 2000]:
            output = chatgpt_web.format_capsule_output(capsule, "https://chatgpt.com/c/test", max_chars=max_chars)
            self.assertLessEqual(len(output), max_chars, f"Exceeded max_chars={max_chars}")
            parsed = json.loads(output)
            self.assertIsInstance(parsed, dict)
            self.assertIn("status", parsed)
            self.assertIn("url", parsed)

    def test_format_small_envelope_when_capsule_too_large(self):
        """When reduced capsule is still too large, returns status-only envelope."""
        capsule = {"conclusion": "F" * 3000, "evidence": [{"claim": "x", "source": "y"}] * 50,
                    "uncertainties": ["u"] * 20, "actions_for_codex": ["a"] * 20}
        output = chatgpt_web.format_capsule_output(capsule, "https://chatgpt.com/c/test", max_chars=150)
        self.assertLessEqual(len(output), 150)
        parsed = json.loads(output)
        self.assertEqual(parsed["status"], "ok")
        self.assertTrue(parsed["truncated"])
        self.assertIsNone(parsed["capsule"])

    def test_format_capsule_with_delegation_status_in_limit(self):
        """delegation_status is included in envelope and respects max_chars."""
        capsule = {"conclusion": "ok", "evidence": [], "uncertainties": [], "actions_for_codex": []}
        output = chatgpt_web.format_capsule_output(
            capsule, "https://chatgpt.com/c/test", max_chars=500, delegation_status="COMPLETED",
        )
        self.assertLessEqual(len(output), 500)
        parsed = json.loads(output)
        self.assertEqual(parsed["delegation_status"], "COMPLETED")
        self.assertEqual(parsed["status"], "ok")

    def test_format_capsule_delegation_status_counted_in_truncation(self):
        """delegation_status field is present even in truncated output."""
        capsule = {"conclusion": "G" * 3000, "evidence": [], "uncertainties": [], "actions_for_codex": []}
        output = chatgpt_web.format_capsule_output(
            capsule, "https://chatgpt.com/c/test", max_chars=200, delegation_status="COMPLETED",
        )
        self.assertLessEqual(len(output), 200)
        parsed = json.loads(output)
        self.assertEqual(parsed["delegation_status"], "COMPLETED")

    def test_format_extraction_failure_valid_json(self):
        """Extraction failure produces valid JSON."""
        output = chatgpt_web.format_extraction_failure_output(
            "https://chatgpt.com/c/test", "My Topic", max_chars=2000,
        )
        parsed = json.loads(output)
        self.assertEqual(parsed["status"], "extraction_failed")
        self.assertEqual(parsed["url"], "https://chatgpt.com/c/test")
        self.assertEqual(parsed["topic"], "My Topic")

    def test_format_extraction_failure_with_delegation_status(self):
        """Extraction failure includes delegation_status when provided."""
        output = chatgpt_web.format_extraction_failure_output(
            "https://chatgpt.com/c/test", "My Topic", max_chars=2000,
            delegation_status="CAPSULE_FAILED",
        )
        parsed = json.loads(output)
        self.assertEqual(parsed["delegation_status"], "CAPSULE_FAILED")

    def test_format_extraction_failure_too_small_raises(self):
        """Extraction failure raises ValueError for impossibly small max_chars."""
        with self.assertRaises(ValueError):
            chatgpt_web.format_extraction_failure_output(
                "https://chatgpt.com/c/test", "My Topic", max_chars=10,
            )

    def test_format_extraction_failure_compact_fallback(self):
        """When full envelope is too large, drops hint and topic."""
        output = chatgpt_web.format_extraction_failure_output(
            "https://chatgpt.com/c/test", "My Very Long Topic Name", max_chars=120,
        )
        self.assertLessEqual(len(output), 120)
        parsed = json.loads(output)
        self.assertEqual(parsed["status"], "extraction_failed")


class TestReceiptFormatting(unittest.TestCase):
    """Test receipt-only output formatting."""

    def test_format_receipt(self):
        output = chatgpt_web.format_receipt_output("Test Topic", "https://chatgpt.com/c/123", "COMPLETED")
        self.assertIn("STATUS: COMPLETED", output)
        self.assertIn("TOPIC: Test Topic", output)
        self.assertIn("URL: https://chatgpt.com/c/123", output)


class TestPromptAugmentation(unittest.TestCase):
    """Test prompt augmentation for capsule mode."""

    def test_augment_adds_protocol(self):
        original = "Research this topic."
        augmented = chatgpt_web.augment_prompt_for_capsule(original)
        self.assertIn(original, augmented)
        self.assertIn("<codex_capsule>", augmented)
        self.assertIn("<codex_output_protocol>", augmented)


class TestTaskLock(unittest.TestCase):
    """Test atomic single-task locking."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.lock_path = Path(self.temp_dir) / "test.lock"
        self.patcher = patch('chatgpt_web.LOCK_PATH', self.lock_path)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        if self.lock_path.exists():
            self.lock_path.unlink()

    def test_acquire_success(self):
        lock = chatgpt_web.TaskLock("test-run-1", "ask")
        self.assertTrue(lock.acquire())
        self.assertTrue(lock.acquired)
        lock.release()

    def test_acquire_conflict(self):
        lock1 = chatgpt_web.TaskLock("test-run-1", "ask")
        lock1.acquire()
        lock2 = chatgpt_web.TaskLock("test-run-2", "ask")
        self.assertFalse(lock2.acquire())
        lock1.release()

    def test_context_manager(self):
        with chatgpt_web.TaskLock("test-run-1", "ask") as lock:
            self.assertTrue(lock.acquired)
            lock2 = chatgpt_web.TaskLock("test-run-2", "ask")
            self.assertFalse(lock2.acquire())

    def test_stale_lock_with_dead_pid_recovered(self):
        """Stale lock with dead PID is recovered."""
        stale_time = (dt.datetime.now() - dt.timedelta(minutes=11)).isoformat()
        self.lock_path.write_text(json.dumps({
            "run_id": "stale-run",
            "pid": 999999,
            "started_at": stale_time,
            "cmd_type": "ask"
        }))
        lock = chatgpt_web.TaskLock("new-run", "ask")
        self.assertTrue(lock.acquire())
        lock.release()

    @patch('chatgpt_web.pid_is_alive', return_value=True)
    def test_stale_lock_with_live_positive_pid_retained(self, mock_alive):
        """Stale lock with live positive PID is NOT stolen."""
        stale_time = (dt.datetime.now() - dt.timedelta(minutes=11)).isoformat()
        self.lock_path.write_text(json.dumps({
            "run_id": "live-run",
            "pid": os.getpid(),
            "started_at": stale_time,
            "cmd_type": "delegate"
        }))
        lock = chatgpt_web.TaskLock("new-run", "ask")
        self.assertFalse(lock.acquire())
        mock_alive.assert_called()

    def test_stale_lock_with_pid_zero_recovered(self):
        """PID 0 is malformed (not a positive integer); stale lock is recovered."""
        stale_time = (dt.datetime.now() - dt.timedelta(minutes=11)).isoformat()
        self.lock_path.write_text(json.dumps({
            "run_id": "pid-zero-run",
            "pid": 0,
            "started_at": stale_time,
            "cmd_type": "ask"
        }))
        lock = chatgpt_web.TaskLock("new-run", "ask")
        self.assertTrue(lock.acquire())
        lock.release()

    def test_stale_lock_with_negative_pid_recovered(self):
        """Negative PID is malformed; stale lock is recovered."""
        stale_time = (dt.datetime.now() - dt.timedelta(minutes=11)).isoformat()
        self.lock_path.write_text(json.dumps({
            "run_id": "neg-pid-run",
            "pid": -5,
            "started_at": stale_time,
            "cmd_type": "ask"
        }))
        lock = chatgpt_web.TaskLock("new-run", "ask")
        self.assertTrue(lock.acquire())
        lock.release()

    def test_malformed_lock_file_not_recovered(self):
        """Malformed lock file is not silently recovered."""
        self.lock_path.write_text("not json{{{")
        lock = chatgpt_web.TaskLock("new-run", "ask")
        self.assertFalse(lock.acquire())

    def test_lock_with_no_pid_field_recovered(self):
        """Lock file missing pid field (malformed) is recovered after stale."""
        stale_time = (dt.datetime.now() - dt.timedelta(minutes=11)).isoformat()
        self.lock_path.write_text(json.dumps({
            "run_id": "no-pid-run",
            "started_at": stale_time,
        }))
        lock = chatgpt_web.TaskLock("new-run", "ask")
        self.assertTrue(lock.acquire())
        lock.release()


class TestMetricsRecording(unittest.TestCase):
    """Test non-sensitive metrics recording."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.metrics_path = Path(self.temp_dir) / "metrics.jsonl"
        self.patcher = patch('chatgpt_web.METRICS_PATH', self.metrics_path)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        if self.metrics_path.exists():
            self.metrics_path.unlink()

    def test_record_metrics(self):
        chatgpt_web.record_metrics(
            run_id="test-123",
            return_mode="capsule",
            success=True,
            response_chars=5000,
            printed_chars=500,
            minimize_ok=True,
            cleanup_ok=True
        )
        self.assertTrue(self.metrics_path.exists())
        lines = self.metrics_path.read_text().strip().split("\n")
        self.assertEqual(len(lines), 1)
        entry = json.loads(lines[0])
        self.assertEqual(entry["run_id"], "test-123")
        self.assertEqual(entry["return_mode"], "capsule")
        self.assertTrue(entry["success"])
        self.assertEqual(entry["response_chars"], 5000)
        self.assertEqual(entry["printed_chars"], 500)
        self.assertEqual(entry["estimated_avoided_chars"], 4500)
        self.assertTrue(entry["minimize_ok"])
        self.assertTrue(entry["cleanup_ok"])
        self.assertFalse(entry["kept_open"])

    def test_metrics_no_sensitive_data(self):
        chatgpt_web.record_metrics(
            run_id="test-456",
            return_mode="capsule",
            success=True,
            response_chars=1000,
            printed_chars=200
        )
        content = self.metrics_path.read_text()
        sensitive_terms = ["prompt", "answer", "cookie", "api_key", "password", "token_value"]
        for term in sensitive_terms:
            self.assertNotIn(term, content.lower())


class TestConversationRouting(unittest.TestCase):
    """Test conversation routing behavior."""

    def test_select_topic_returns_last(self):
        state = {
            "last_topic_id": "topic-2",
            "topics": [
                {"id": "topic-1", "title": "First", "url": "https://chatgpt.com/c/1"},
                {"id": "topic-2", "title": "Second", "url": "https://chatgpt.com/c/2"}
            ]
        }
        topic = chatgpt_web.select_topic(state)
        self.assertEqual(topic["id"], "topic-2")

    def test_select_topic_by_query(self):
        state = {
            "last_topic_id": "topic-1",
            "topics": [
                {"id": "topic-1", "title": "Python basics", "url": "https://chatgpt.com/c/1"},
                {"id": "topic-2", "title": "JavaScript guide", "url": "https://chatgpt.com/c/2"}
            ]
        }
        topic = chatgpt_web.select_topic(state, "javascript")
        self.assertEqual(topic["id"], "topic-2")

    def test_select_topic_empty(self):
        state = {"last_topic_id": None, "topics": []}
        topic = chatgpt_web.select_topic(state)
        self.assertIsNone(topic)

    def test_conversation_id_extraction(self):
        self.assertEqual(
            chatgpt_web.conversation_id("https://chatgpt.com/c/abc123"),
            "abc123"
        )
        self.assertEqual(
            chatgpt_web.conversation_id("https://chatgpt.com/g/g-xxx/c/abc123"),
            "abc123"
        )
        self.assertIsNone(chatgpt_web.conversation_id("https://chatgpt.com/"))
        self.assertIsNone(chatgpt_web.conversation_id(""))

    def test_response_likely_limited(self):
        self.assertTrue(chatgpt_web.response_likely_limited("You've reached the usage limit"))
        self.assertTrue(chatgpt_web.response_likely_limited("已达到使用上限"))
        self.assertFalse(chatgpt_web.response_likely_limited("Here is your answer"))


class TestOwnedWindowManager(unittest.TestCase):
    """Test target-based owned window management."""

    def test_marker_url_uses_allowed_chatgpt_fragment(self):
        mgr = chatgpt_web.OwnedWindowManager("abc123")
        self.assertEqual(mgr.marker_url, "https://chatgpt.com/#chatgpt-web-abc123")
        self.assertIn("#chatgpt-web-", mgr.marker_url)

    def test_marker_url_does_not_create_conversation_path(self):
        mgr = chatgpt_web.OwnedWindowManager("test-run")
        self.assertNotIn("/c/", mgr.marker_url)

    @patch('chatgpt_web.run')
    def test_open_marker_uses_isolated_background_session(self, mock_run):
        mock_run.return_value = ('{"page":"tab-1","url":"https://chatgpt.com/#chatgpt-web-abc"}', 0)
        mgr = chatgpt_web.OwnedWindowManager("abc")
        target_id = mgr.open_marker()
        self.assertEqual(target_id, "tab-1")
        self.assertEqual(mgr.target_id, "tab-1")
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd, ["opencli", "browser", "chatgptwebabc", "--window", "background", "open", "https://chatgpt.com/#chatgpt-web-abc"])

    @patch('chatgpt_web.run')
    def test_open_marker_never_uses_unscoped_browser_open(self, mock_run):
        mock_run.return_value = ('{"page":"tab-1","url":"https://chatgpt.com/#chatgpt-web-abc"}', 0)
        mgr = chatgpt_web.OwnedWindowManager("abc")
        mgr.open_marker()
        cmd = mock_run.call_args[0][0]
        self.assertNotEqual(cmd[:3], ["opencli", "browser", "open"])

    @patch('chatgpt_web.run')
    def test_open_marker_returns_none_on_failure(self, mock_run):
        mock_run.return_value = ("error", 1)
        mgr = chatgpt_web.OwnedWindowManager("abc")
        target_id = mgr.open_marker()
        self.assertIsNone(target_id)
        self.assertIsNone(mgr.target_id)

    @patch('chatgpt_web.run')
    def test_open_marker_with_prefix_notice_text(self, mock_run):
        """Parser handles stdout with surrounding notice text from tab new."""
        mock_run.return_value = ('Creating tab...\n{"page":"tab-7","url":"https://chatgpt.com/#chatgpt-web-abc"}\nOK', 0)
        mgr = chatgpt_web.OwnedWindowManager("abc")
        target_id = mgr.open_marker()
        self.assertEqual(target_id, "tab-7")

    @patch('chatgpt_web.run')
    def test_navigate_to_topic_uses_tab_flag(self, mock_run):
        mock_run.return_value = ('{"page":"tab-1"}', 0)
        mgr = chatgpt_web.OwnedWindowManager("abc")
        mgr.target_id = "tab-1"
        result = mgr.navigate_to_topic("https://chatgpt.com/c/xyz")
        self.assertTrue(result)
        cmd = mock_run.call_args[0][0]
        self.assertIn("chatgptwebabc", cmd)
        self.assertIn("--tab", cmd)
        self.assertIn("tab-1", cmd)
        self.assertIn("https://chatgpt.com/c/xyz", cmd)

    @patch('chatgpt_web.run')
    def test_navigate_fails_without_target_id(self, mock_run):
        mgr = chatgpt_web.OwnedWindowManager("abc")
        result = mgr.navigate_to_topic("https://chatgpt.com/c/xyz")
        self.assertFalse(result)
        mock_run.assert_not_called()

    @patch('chatgpt_web.run')
    def test_close_owned_window_releases_unique_session(self, mock_run):
        mock_run.return_value = ("", 0)
        mgr = chatgpt_web.OwnedWindowManager("abc")
        mgr.target_id = "tab-2"
        result = mgr.close_owned_window()
        self.assertTrue(result)
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd, ["opencli", "browser", "chatgptwebabc", "close"])

    @patch('chatgpt_web.run')
    def test_close_owned_window_no_unscoped_close(self, mock_run):
        """Cleanup must never call unscoped 'browser close'."""
        mock_run.return_value = ("", 0)
        mgr = chatgpt_web.OwnedWindowManager("abc")
        mgr.target_id = "tab-1"
        mgr.close_owned_window()
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd, ["opencli", "browser", "chatgptwebabc", "close"])

    @patch('chatgpt_web.run')
    def test_cleanup_returns_false_without_target(self, mock_run):
        mgr = chatgpt_web.OwnedWindowManager("abc")
        result = mgr.cleanup()
        self.assertFalse(result)

    @patch('chatgpt_web.run', return_value=("", 1))
    def test_cleanup_returns_false_on_failure(self, mock_run):
        mgr = chatgpt_web.OwnedWindowManager("abc")
        mgr.target_id = "tab-1"
        result = mgr.cleanup()
        self.assertFalse(result)

    @patch('chatgpt_web.run', side_effect=Exception("boom"))
    def test_cleanup_never_raises(self, mock_run):
        mgr = chatgpt_web.OwnedWindowManager("abc")
        mgr.target_id = "tab-1"
        result = mgr.cleanup()
        self.assertFalse(result)

    @patch('chatgpt_web.platform.system', return_value="Darwin")
    @patch('chatgpt_web.run')
    def test_identify_fails_with_no_windows(self, mock_run, mock_platform):
        mock_run.return_value = ("", 0)
        mgr = chatgpt_web.OwnedWindowManager("test-run-123")
        result = mgr.identify_and_minimize()
        self.assertFalse(result)

    @patch('chatgpt_web.platform.system', return_value="Darwin")
    @patch('chatgpt_web.run')
    def test_identify_fails_with_multiple_matches(self, mock_run, mock_platform):
        mock_run.return_value = ("1:1:https://chatgpt.com/#chatgpt-web-test-run-123\n2:1:https://chatgpt.com/#chatgpt-web-test-run-123", 0)
        mgr = chatgpt_web.OwnedWindowManager("test-run-123")
        result = mgr.identify_and_minimize()
        self.assertFalse(result)

    @patch('chatgpt_web.platform.system', return_value="Darwin")
    @patch('chatgpt_web.run')
    def test_identify_succeeds_with_unique_match(self, mock_run, mock_platform):
        mock_run.side_effect = [
            ("1:1:https://chatgpt.com/#chatgpt-web-test-run-123", 0),
            ("", 0)
        ]
        mgr = chatgpt_web.OwnedWindowManager("test-run-123")
        result = mgr.identify_and_minimize()
        self.assertTrue(result)

    @patch('chatgpt_web.platform.system', return_value="Linux")
    def test_non_darwin_skips_identification(self, mock_platform):
        mgr = chatgpt_web.OwnedWindowManager("test-run")
        result = mgr.identify_and_minimize()
        self.assertTrue(result)


class TestTargetSpecificBrowserOps(unittest.TestCase):
    """Test that browser helper functions pass --tab when target_id is set."""

    @patch('chatgpt_web.run')
    def test_current_url_with_target(self, mock_run):
        mock_run.return_value = ("https://chatgpt.com/c/abc123", 0)
        url = chatgpt_web.current_url("session1", target_id="tab-1")
        self.assertEqual(url, "https://chatgpt.com/c/abc123")
        cmd = mock_run.call_args[0][0]
        self.assertIn("--tab", cmd)
        self.assertIn("tab-1", cmd)
        self.assertIn("session1", cmd)

    @patch('chatgpt_web.run')
    def test_current_url_without_target(self, mock_run):
        mock_run.return_value = ("https://chatgpt.com/c/abc123", 0)
        url = chatgpt_web.current_url("session1")
        cmd = mock_run.call_args[0][0]
        self.assertNotIn("--tab", cmd)

    @patch('chatgpt_web.run')
    def test_newest_assistant_text_with_target(self, mock_run):
        mock_run.return_value = ("Here is the answer", 0)
        text = chatgpt_web.newest_assistant_text("session1", target_id="tab-3")
        self.assertEqual(text, "Here is the answer")
        cmd = mock_run.call_args_list[0][0][0]
        self.assertIn("--tab", cmd)
        self.assertIn("tab-3", cmd)


class TestComposerDiscovery(unittest.TestCase):
    """Test composer lookup against the live DOM rather than state summaries."""

    @patch('chatgpt_web.run')
    def test_returns_prompt_textarea_found_by_dom_eval(self, mock_run):
        mock_run.return_value = ("CHATGPT_WEB_COMPOSER:0", 0)
        selector = chatgpt_web.find_composer_selector("session1", target_id="tab-4")
        self.assertEqual(selector, "#prompt-textarea")
        cmd = mock_run.call_args[0][0]
        self.assertIn("eval", cmd)
        self.assertNotIn("state", cmd)
        self.assertIn("--tab", cmd)
        self.assertIn("tab-4", cmd)

    @patch('chatgpt_web.run')
    def test_returns_accessible_textarea_fallback(self, mock_run):
        mock_run.return_value = ("CHATGPT_WEB_COMPOSER:3", 0)
        selector = chatgpt_web.find_composer_selector("session1")
        self.assertEqual(selector, 'textarea[aria-label*="ChatGPT"]')

    @patch('chatgpt_web.run')
    def test_returns_none_when_dom_has_no_composer(self, mock_run):
        mock_run.return_value = ("CHATGPT_WEB_COMPOSER:none", 0)
        self.assertIsNone(chatgpt_web.find_composer_selector("session1"))


class TestPromptSubmission(unittest.TestCase):
    """Test submission through the send button in the owned page context."""

    @patch('chatgpt_web.run')
    def test_submits_with_dom_click_in_owned_tab(self, mock_run):
        mock_run.return_value = ("CHATGPT_WEB_SUBMIT:clicked", 0)
        self.assertTrue(chatgpt_web.submit_prompt("session1", target_id="tab-5"))
        cmd = mock_run.call_args[0][0]
        self.assertIn("eval", cmd)
        self.assertIn("--tab", cmd)
        self.assertIn("tab-5", cmd)
        self.assertIn("send-button", cmd[-1])

    @patch('chatgpt_web.run')
    def test_refuses_when_send_button_is_unavailable(self, mock_run):
        mock_run.return_value = ("CHATGPT_WEB_SUBMIT:unavailable", 0)
        self.assertFalse(chatgpt_web.submit_prompt("session1", target_id="tab-5"))


class TestReturnModeDefaults(unittest.TestCase):
    """Test return mode defaults and validation."""

    def test_default_return_mode(self):
        self.assertEqual(chatgpt_web.DEFAULT_RETURN_MODE, "capsule")

    def test_valid_return_modes(self):
        self.assertIn("receipt", chatgpt_web.RETURN_MODES)
        self.assertIn("capsule", chatgpt_web.RETURN_MODES)
        self.assertIn("full", chatgpt_web.RETURN_MODES)

    def test_default_max_chars(self):
        self.assertEqual(chatgpt_web.DEFAULT_MAX_CHARS, 2000)


class TestInitializeFailureCleanup(unittest.TestCase):
    """Test that cleanup runs even when initialization fails early."""

    @patch('chatgpt_web.record_metrics')
    @patch('chatgpt_web.ensure_connected', side_effect=RuntimeError("disconnected"))
    @patch('chatgpt_web.TaskLock.__enter__', return_value=MagicMock())
    @patch('chatgpt_web.TaskLock.__exit__', return_value=False)
    def test_cleanup_runs_on_ensure_connected_failure(self, mock_exit, mock_enter, mock_connect, mock_metrics):
        """Even if ensure_connected fails, window_mgr.cleanup() is called."""
        args = argparse.Namespace(
            new=True, title=None, topic=None, prompt="test", search=False,
            return_mode="capsule", max_chars=2000, delegate=False,
            keep_open=False, timeout=120,
        )
        with self.assertRaises(RuntimeError):
            chatgpt_web.ask(args)
        mock_metrics.assert_called_once()


class TestCapsuleSuccessMetadata(unittest.TestCase):
    """Test that capsule mode sets success correctly."""

    def _make_args(self, **overrides):
        defaults = dict(
            new=True, title=None, topic=None, prompt="test", search=False,
            return_mode="capsule", max_chars=2000, delegate=False,
            keep_open=False, timeout=120,
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def _setup_mocks(self):
        """Return a dict of patchers and mock objects for ask() testing."""
        patches = {
            "record_metrics": patch("chatgpt_web.record_metrics"),
            "lock_enter": patch("chatgpt_web.TaskLock.__enter__", return_value=MagicMock()),
            "lock_exit": patch("chatgpt_web.TaskLock.__exit__", return_value=False),
            "ensure_connected": patch("chatgpt_web.ensure_connected"),
            "load_state": patch("chatgpt_web.load_state"),
            "upsert_topic": patch("chatgpt_web.upsert_topic"),
            "select_topic": patch("chatgpt_web.select_topic"),
            "owm": patch("chatgpt_web.OwnedWindowManager"),
            "current_url": patch("chatgpt_web.current_url"),
            "wait": patch("chatgpt_web.wait_until_done"),
            "assistant": patch("chatgpt_web.newest_assistant_text"),
            "submit": patch("chatgpt_web.submit_prompt", return_value=True),
            "run": patch("chatgpt_web.run"),
            "print": patch("builtins.print"),
        }
        mocks = {k: p.start() for k, p in patches.items()}
        mocks["_patches"] = patches
        mocks["ensure_connected"].return_value = "connected"
        mocks["load_state"].return_value = {"version": 2, "last_topic_id": None, "topics": []}
        mocks["select_topic"].return_value = {
            "id": "t1", "title": "Test Topic", "url": "https://chatgpt.com/c/abc",
        }
        owm_inst = MagicMock()
        owm_inst.open_marker.return_value = "tab-1"
        owm_inst.is_darwin = False
        owm_inst.navigate_to_topic.return_value = True
        owm_inst.cleanup.return_value = True
        mocks["owm"].return_value = owm_inst
        mocks["run"].return_value = ("CHATGPT_WEB_COMPOSER:0", 0)
        mocks["current_url"].return_value = "https://chatgpt.com/c/abc"
        return mocks

    def _stop_mocks(self, mocks):
        for p in mocks["_patches"].values():
            p.stop()

    def test_capsule_success_true_on_valid_capsule(self):
        """success=True only when valid capsule output is printed."""
        mocks = self._setup_mocks()
        try:
            mocks["assistant"].return_value = (
                '<codex_capsule>{"conclusion":"test","evidence":[],"uncertainties":[],"actions_for_codex":[]}</codex_capsule>'
            )
            chatgpt_web.ask(self._make_args())
            metrics_call = mocks["record_metrics"].call_args
            self.assertTrue(metrics_call[1]["success"])
        finally:
            self._stop_mocks(mocks)

    def test_capsule_success_false_on_extraction_failure(self):
        """success=False when capsule extraction fails."""
        mocks = self._setup_mocks()
        try:
            mocks["assistant"].return_value = "Just a plain text answer without any capsule."
            chatgpt_web.ask(self._make_args())
            printed = mocks["print"].call_args[0][0]
            parsed = json.loads(printed)
            self.assertEqual(parsed["status"], "extraction_failed")
            metrics_call = mocks["record_metrics"].call_args
            self.assertFalse(metrics_call[1]["success"])
        finally:
            self._stop_mocks(mocks)

    def test_receipt_success_true(self):
        """receipt mode sets success=True."""
        mocks = self._setup_mocks()
        try:
            mocks["assistant"].return_value = "Some answer."
            chatgpt_web.ask(self._make_args(return_mode="receipt"))
            metrics_call = mocks["record_metrics"].call_args
            self.assertTrue(metrics_call[1]["success"])
        finally:
            self._stop_mocks(mocks)

    def test_full_success_true(self):
        """full mode sets success=True."""
        mocks = self._setup_mocks()
        try:
            mocks["assistant"].return_value = "Complete answer text."
            chatgpt_web.ask(self._make_args(return_mode="full"))
            metrics_call = mocks["record_metrics"].call_args
            self.assertTrue(metrics_call[1]["success"])
        finally:
            self._stop_mocks(mocks)

    def test_submit_uses_owned_tab_dom_submission(self):
        """Prepared content is submitted through the isolated page helper."""
        mocks = self._setup_mocks()
        try:
            mocks["assistant"].return_value = (
                '<codex_capsule>{"conclusion":"ok","evidence":[],"uncertainties":[],"actions_for_codex":[]}</codex_capsule>'
            )
            chatgpt_web.ask(self._make_args())
            commands = [entry[0][0] for entry in mocks["run"].call_args_list]
            mocks["submit"].assert_called_once()
            self.assertFalse(any("keys" in cmd and "Enter" in cmd for cmd in commands))
        finally:
            self._stop_mocks(mocks)

    def test_delegate_capsule_respects_max_chars(self):
        """delegate=True capsule output with tight max_chars is valid JSON within limit."""
        mocks = self._setup_mocks()
        try:
            mocks["assistant"].return_value = (
                '<codex_capsule>{"conclusion":"ok","evidence":[],"uncertainties":[],"actions_for_codex":[]}</codex_capsule>'
            )
            max_chars = 150
            chatgpt_web.ask(self._make_args(delegate=True, max_chars=max_chars))
            printed = mocks["print"].call_args[0][0]
            self.assertLessEqual(len(printed), max_chars)
            parsed = json.loads(printed)
            self.assertIn("delegation_status", parsed)
            self.assertEqual(parsed["delegation_status"], "COMPLETED")
        finally:
            self._stop_mocks(mocks)

    def test_capsule_too_small_raises_value_error(self):
        """impossibly small max_chars raises ValueError before printing."""
        mocks = self._setup_mocks()
        try:
            mocks["assistant"].return_value = (
                '<codex_capsule>{"conclusion":"test","evidence":[],"uncertainties":[],"actions_for_codex":[]}</codex_capsule>'
            )
            with self.assertRaises(ValueError):
                chatgpt_web.ask(self._make_args(max_chars=10))
        finally:
            self._stop_mocks(mocks)

    def test_extraction_failure_too_small_raises_value_error(self):
        """impossibly small max_chars for extraction failure raises ValueError."""
        mocks = self._setup_mocks()
        try:
            mocks["assistant"].return_value = "Plain text, no capsule."
            with self.assertRaises(ValueError):
                chatgpt_web.ask(self._make_args(max_chars=10))
        finally:
            self._stop_mocks(mocks)


class TestLockParentDirectory(unittest.TestCase):
    """Test that lock creation works even when parent directory doesn't exist."""

    def test_acquire_creates_parent_directory(self):
        """Lock acquire succeeds when parent directory is initially missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = Path(tmpdir) / "nonexistent" / "deep" / "state"
            lock_path = nested / "test.lock"
            with patch('chatgpt_web.LOCK_PATH', lock_path):
                lock = chatgpt_web.TaskLock("test-run", "ask")
                self.assertTrue(lock.acquire())
                self.assertTrue(lock_path.exists())
                lock.release()
                # Lock file removed, parent dirs remain
                self.assertFalse(lock_path.exists())

    def test_acquire_creates_parent_directory_atomically(self):
        """Lock file is created atomically even after parent dir creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = Path(tmpdir) / "new_state_dir"
            lock_path = nested / "test.lock"
            with patch('chatgpt_web.LOCK_PATH', lock_path):
                lock1 = chatgpt_web.TaskLock("run-1", "ask")
                self.assertTrue(lock1.acquire())
                # Second acquire must fail (atomic)
                lock2 = chatgpt_web.TaskLock("run-2", "ask")
                self.assertFalse(lock2.acquire())
                lock1.release()


class TestDoctorLock(unittest.TestCase):
    """Test that a connection probe cannot race active browser work."""

    @patch("chatgpt_web.ensure_connected", return_value="connected")
    @patch("chatgpt_web.TaskLock")
    def test_locked_connection_check_uses_doctor_lock(self, mock_lock, mock_connect):
        self.assertEqual(chatgpt_web.locked_connection_check(), "connected")
        self.assertEqual(mock_lock.call_args.kwargs["cmd_type"], "doctor")
        mock_lock.return_value.__enter__.assert_called_once()
        mock_connect.assert_called_once()


class TestKeepOpenFlag(unittest.TestCase):
    """Test --keep-open flag behavior in ask()."""

    def _make_args(self, **overrides):
        defaults = dict(
            new=True, title=None, topic=None, prompt="test", search=False,
            return_mode="capsule", max_chars=2000, delegate=False,
            keep_open=False, timeout=120,
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def _setup_mocks(self):
        patches = {
            "record_metrics": patch("chatgpt_web.record_metrics"),
            "lock_enter": patch("chatgpt_web.TaskLock.__enter__", return_value=MagicMock()),
            "lock_exit": patch("chatgpt_web.TaskLock.__exit__", return_value=False),
            "ensure_connected": patch("chatgpt_web.ensure_connected"),
            "load_state": patch("chatgpt_web.load_state"),
            "upsert_topic": patch("chatgpt_web.upsert_topic"),
            "select_topic": patch("chatgpt_web.select_topic"),
            "owm": patch("chatgpt_web.OwnedWindowManager"),
            "current_url": patch("chatgpt_web.current_url"),
            "wait": patch("chatgpt_web.wait_until_done"),
            "assistant": patch("chatgpt_web.newest_assistant_text"),
            "submit": patch("chatgpt_web.submit_prompt", return_value=True),
            "run": patch("chatgpt_web.run"),
            "print": patch("builtins.print"),
        }
        mocks = {k: p.start() for k, p in patches.items()}
        mocks["_patches"] = patches
        mocks["ensure_connected"].return_value = "connected"
        mocks["load_state"].return_value = {"version": 2, "last_topic_id": None, "topics": []}
        mocks["select_topic"].return_value = {
            "id": "t1", "title": "Test Topic", "url": "https://chatgpt.com/c/abc",
        }
        owm_inst = MagicMock()
        owm_inst.open_marker.return_value = "tab-1"
        owm_inst.is_darwin = False
        owm_inst.navigate_to_topic.return_value = True
        owm_inst.cleanup.return_value = True
        mocks["owm"].return_value = owm_inst
        mocks["run"].return_value = ("CHATGPT_WEB_COMPOSER:0", 0)
        mocks["current_url"].return_value = "https://chatgpt.com/c/abc"
        return mocks

    def _stop_mocks(self, mocks):
        for p in mocks["_patches"].values():
            p.stop()

    def test_default_success_closes_owned_tab(self):
        """Default path (keep_open=False) calls window_mgr.cleanup()."""
        mocks = self._setup_mocks()
        try:
            mocks["assistant"].return_value = (
                '<codex_capsule>{"conclusion":"ok","evidence":[],"uncertainties":[],"actions_for_codex":[]}</codex_capsule>'
            )
            chatgpt_web.ask(self._make_args(keep_open=False))
            owm_inst = mocks["owm"].return_value
            owm_inst.cleanup.assert_called_once()
            metrics_call = mocks["record_metrics"].call_args
            self.assertTrue(metrics_call[1]["cleanup_ok"])
        finally:
            self._stop_mocks(mocks)

    def test_default_exception_closes_owned_tab(self):
        """Default path (keep_open=False) calls cleanup even on exception."""
        mocks = self._setup_mocks()
        try:
            mocks["assistant"].side_effect = RuntimeError("boom")
            with self.assertRaises(RuntimeError):
                chatgpt_web.ask(self._make_args(keep_open=False))
            owm_inst = mocks["owm"].return_value
            owm_inst.cleanup.assert_called_once()
        finally:
            self._stop_mocks(mocks)

    def test_keep_open_success_does_not_close_owned_tab(self):
        """With keep_open=True, cleanup() is NOT called on success."""
        mocks = self._setup_mocks()
        try:
            mocks["assistant"].return_value = (
                '<codex_capsule>{"conclusion":"ok","evidence":[],"uncertainties":[],"actions_for_codex":[]}</codex_capsule>'
            )
            chatgpt_web.ask(self._make_args(keep_open=True))
            owm_inst = mocks["owm"].return_value
            owm_inst.cleanup.assert_not_called()
            metrics_call = mocks["record_metrics"].call_args
            self.assertFalse(metrics_call[1]["cleanup_ok"])
            self.assertTrue(metrics_call[1]["kept_open"])
        finally:
            self._stop_mocks(mocks)

    def test_keep_open_exception_does_not_close_owned_tab(self):
        """With keep_open=True, cleanup() is NOT called even on exception."""
        mocks = self._setup_mocks()
        try:
            mocks["assistant"].side_effect = RuntimeError("boom")
            with self.assertRaises(RuntimeError):
                chatgpt_web.ask(self._make_args(keep_open=True))
            owm_inst = mocks["owm"].return_value
            owm_inst.cleanup.assert_not_called()
            metrics_call = mocks["record_metrics"].call_args
            self.assertFalse(metrics_call[1]["cleanup_ok"])
            self.assertTrue(metrics_call[1]["kept_open"])
        finally:
            self._stop_mocks(mocks)


class TestDiscoverSelectBoundTabs(unittest.TestCase):
    """Test that discover/select uses bound tabs, not unbound browser operations."""

    @patch('chatgpt_web.ensure_connected')
    @patch('chatgpt_web.run')
    @patch('chatgpt_web.OwnedWindowManager')
    @patch('chatgpt_web.TaskLock.__enter__', return_value=MagicMock())
    @patch('chatgpt_web.TaskLock.__exit__', return_value=False)
    def test_discover_uses_bound_eval(self, mock_exit, mock_enter, mock_owm_cls, mock_run, mock_conn):
        """discover evaluates JS with --tab <targetId>."""
        owm_inst = MagicMock()
        owm_inst.open_marker.return_value = "tab-42"
        owm_inst.is_darwin = False
        owm_inst.navigate_to_topic.return_value = True
        mock_owm_cls.return_value = owm_inst
        mock_run.return_value = ('[]', 0)
        chatgpt_web.discover_topics()
        eval_call = mock_run.call_args_list[-1]
        cmd = eval_call[0][0]
        self.assertIn("--tab", cmd)
        self.assertIn("tab-42", cmd)

    @patch('chatgpt_web.ensure_connected')
    @patch('chatgpt_web.run')
    @patch('chatgpt_web.OwnedWindowManager')
    @patch('chatgpt_web.TaskLock.__enter__', return_value=MagicMock())
    @patch('chatgpt_web.TaskLock.__exit__', return_value=False)
    def test_discover_no_unscoped_browser_close(self, mock_exit, mock_enter, mock_owm_cls, mock_run, mock_conn):
        """discover does NOT call 'opencli browser close' (unscoped)."""
        owm_inst = MagicMock()
        owm_inst.open_marker.return_value = "tab-42"
        owm_inst.is_darwin = False
        owm_inst.navigate_to_topic.return_value = True
        mock_owm_cls.return_value = owm_inst
        mock_run.return_value = ('[]', 0)
        chatgpt_web.discover_topics()
        for c in mock_run.call_args_list:
            cmd = c[0][0]
            self.assertNotEqual(
                cmd[:3], ["opencli", "browser", "close"],
                f"Found unscoped 'browser close' in: {cmd}"
            )

    @patch('chatgpt_web.ensure_connected')
    @patch('chatgpt_web.run')
    @patch('chatgpt_web.OwnedWindowManager')
    @patch('chatgpt_web.TaskLock.__enter__', return_value=MagicMock())
    @patch('chatgpt_web.TaskLock.__exit__', return_value=False)
    def test_discover_no_unscoped_browser_open(self, mock_exit, mock_enter, mock_owm_cls, mock_run, mock_conn):
        """discover does NOT call 'opencli browser open' (unscoped)."""
        owm_inst = MagicMock()
        owm_inst.open_marker.return_value = "tab-42"
        owm_inst.is_darwin = False
        owm_inst.navigate_to_topic.return_value = True
        mock_owm_cls.return_value = owm_inst
        mock_run.return_value = ('[]', 0)
        chatgpt_web.discover_topics()
        for c in mock_run.call_args_list:
            cmd = c[0][0]
            self.assertNotEqual(
                cmd[:3], ["opencli", "browser", "open"],
                f"Found unscoped 'browser open' in: {cmd}"
            )

    @patch('chatgpt_web.ensure_connected')
    @patch('chatgpt_web.run')
    @patch('chatgpt_web.OwnedWindowManager')
    @patch('chatgpt_web.TaskLock.__enter__')
    def test_discover_lock_conflict_no_tab_created(self, mock_enter, mock_owm_cls, mock_run, mock_conn):
        """When lock fails, no tab is created."""
        mock_enter.side_effect = RuntimeError("Another task is already running")
        with self.assertRaises(RuntimeError):
            chatgpt_web.discover_topics()
        mock_conn.assert_not_called()
        mock_owm_cls.assert_not_called()
        mock_run.assert_not_called()

    @patch('chatgpt_web.ensure_connected')
    @patch('chatgpt_web.run')
    @patch('chatgpt_web.OwnedWindowManager')
    @patch('chatgpt_web.TaskLock.__enter__', return_value=MagicMock())
    @patch('chatgpt_web.TaskLock.__exit__', return_value=False)
    def test_discover_cleanup_closes_owned_tab(self, mock_exit, mock_enter, mock_owm_cls, mock_run, mock_conn):
        """discover calls window_mgr.cleanup() in finally."""
        owm_inst = MagicMock()
        owm_inst.open_marker.return_value = "tab-42"
        owm_inst.is_darwin = False
        owm_inst.navigate_to_topic.return_value = True
        mock_owm_cls.return_value = owm_inst
        mock_run.return_value = ('[]', 0)
        chatgpt_web.discover_topics()
        owm_inst.cleanup.assert_called_once()


class TestIdentifyAndMinimizeSharedWindow(unittest.TestCase):
    """Test that identify_and_minimize rejects shared windows."""

    @patch('chatgpt_web.platform.system', return_value="Darwin")
    @patch('chatgpt_web.run')
    def test_sole_tab_allows_minimize(self, mock_run, mock_platform):
        """Marker tab is the only tab in window → allow minimize."""
        mock_run.side_effect = [
            ("1:1:https://chatgpt.com/#chatgpt-web-test-run-123", 0),
            ("", 0),
        ]
        mgr = chatgpt_web.OwnedWindowManager("test-run-123")
        result = mgr.identify_and_minimize()
        self.assertTrue(result)

    @patch('chatgpt_web.platform.system', return_value="Darwin")
    @patch('chatgpt_web.run')
    def test_shared_window_refuses_minimize(self, mock_run, mock_platform):
        """Marker tab shares window with other tabs → refuse minimize."""
        mock_run.return_value = ("1:3:https://chatgpt.com/#chatgpt-web-test-run-123", 0)
        mgr = chatgpt_web.OwnedWindowManager("test-run-123")
        result = mgr.identify_and_minimize()
        self.assertFalse(result)
        # No minimize script should have been run
        for c in mock_run.call_args_list:
            cmd = c[0][0]
            if cmd[0] == "osascript" and "-e" in cmd:
                self.assertNotIn("set minimized", cmd[2])

    @patch('chatgpt_web.platform.system', return_value="Darwin")
    @patch('chatgpt_web.run')
    def test_two_tabs_in_window_refuses_minimize(self, mock_run, mock_platform):
        """Window with 2 tabs (one owned) → refuse minimize."""
        mock_run.return_value = ("1:2:https://chatgpt.com/#chatgpt-web-test-run-123", 0)
        mgr = chatgpt_web.OwnedWindowManager("test-run-123")
        result = mgr.identify_and_minimize()
        self.assertFalse(result)

    @patch('chatgpt_web.platform.system', return_value="Darwin")
    @patch('chatgpt_web.run')
    def test_refuse_minimize_returns_false_to_caller(self, mock_run, mock_platform):
        """When shared window detected, caller should abort."""
        mock_run.return_value = ("1:5:https://chatgpt.com/#chatgpt-web-test-run-123", 0)
        mgr = chatgpt_web.OwnedWindowManager("test-run-123")
        result = mgr.identify_and_minimize()
        self.assertFalse(result)


class TestSharedWindowAbortsPrompt(unittest.TestCase):
    """Test that shared window detection aborts before sending prompt."""

    def _make_args(self, **overrides):
        defaults = dict(
            new=True, title=None, topic=None, prompt="test", search=False,
            return_mode="capsule", max_chars=2000, delegate=False,
            keep_open=False, timeout=120,
        )
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def _setup_mocks(self):
        patches = {
            "record_metrics": patch("chatgpt_web.record_metrics"),
            "lock_enter": patch("chatgpt_web.TaskLock.__enter__", return_value=MagicMock()),
            "lock_exit": patch("chatgpt_web.TaskLock.__exit__", return_value=False),
            "ensure_connected": patch("chatgpt_web.ensure_connected"),
            "load_state": patch("chatgpt_web.load_state"),
            "upsert_topic": patch("chatgpt_web.upsert_topic"),
            "select_topic": patch("chatgpt_web.select_topic"),
            "owm": patch("chatgpt_web.OwnedWindowManager"),
            "current_url": patch("chatgpt_web.current_url"),
            "wait": patch("chatgpt_web.wait_until_done"),
            "assistant": patch("chatgpt_web.newest_assistant_text"),
            "run": patch("chatgpt_web.run"),
            "print": patch("builtins.print"),
        }
        mocks = {k: p.start() for k, p in patches.items()}
        mocks["_patches"] = patches
        mocks["ensure_connected"].return_value = "connected"
        mocks["load_state"].return_value = {"version": 2, "last_topic_id": None, "topics": []}
        mocks["select_topic"].return_value = {
            "id": "t1", "title": "Test Topic", "url": "https://chatgpt.com/c/abc",
        }
        mocks["run"].return_value = ("CHATGPT_WEB_COMPOSER:0", 0)
        mocks["current_url"].return_value = "https://chatgpt.com/c/abc"
        return mocks

    def _stop_mocks(self, mocks):
        for p in mocks["_patches"].values():
            p.stop()

    def test_shared_window_aborts_before_sending_prompt(self):
        """When identify_and_minimize returns False, ask() aborts before type/enter."""
        mocks = self._setup_mocks()
        try:
            owm_inst = MagicMock()
            owm_inst.open_marker.return_value = "tab-1"
            owm_inst.is_darwin = True
            owm_inst.identify_and_minimize.return_value = False
            owm_inst.cleanup.return_value = False
            mocks["owm"].return_value = owm_inst
            with self.assertRaises(RuntimeError) as ctx:
                chatgpt_web.ask(self._make_args())
            self.assertIn("minimize", str(ctx.exception).lower())
            owm_inst.cleanup.assert_called_once()
            mocks["assistant"].assert_not_called()
        finally:
            self._stop_mocks(mocks)

    def test_shared_window_cleanup_only_closes_owned_tab(self):
        """When shared window detected, cleanup() is called (closes owned tab)."""
        mocks = self._setup_mocks()
        try:
            owm_inst = MagicMock()
            owm_inst.open_marker.return_value = "tab-1"
            owm_inst.is_darwin = True
            owm_inst.identify_and_minimize.return_value = False
            owm_inst.cleanup.return_value = False
            mocks["owm"].return_value = owm_inst
            with self.assertRaises(RuntimeError):
                chatgpt_web.ask(self._make_args())
            owm_inst.cleanup.assert_called_once()
            metrics_call = mocks["record_metrics"].call_args
            self.assertFalse(metrics_call[1]["minimize_ok"])
            self.assertFalse(metrics_call[1]["cleanup_ok"])
        finally:
            self._stop_mocks(mocks)


if __name__ == "__main__":
    unittest.main()
