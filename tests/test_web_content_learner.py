import importlib.util
import pathlib
import tempfile
import unittest


MODULE_PATH = (
    pathlib.Path(__file__).resolve().parents[1]
    / "web-content-learner"
    / "scripts"
    / "web_content_learner.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location("web_content_learner", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class WebContentLearnerTest(unittest.TestCase):
    def test_generic_webpage_and_search_are_unsupported(self):
        module = load_module()
        self.assertEqual(module.detect_intent("https://example.com/article"), "unsupported")
        self.assertEqual(module.detect_intent("search for GraphRAG"), "unsupported")

    def test_media_request_defaults_to_transcription(self):
        module = load_module()
        self.assertEqual(
            module.detect_intent("帮我转写 https://youtube.com/watch?v=abc"),
            "transcribe",
        )

    def test_download_builds_media_and_subtitle_command(self):
        module = load_module()
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            return type("Result", (), {"stdout": "/tmp/video.webm\n"})()

        with tempfile.TemporaryDirectory() as output_dir:
            learner = module.MediaLearner(output_dir=output_dir, runner=runner)
            path = learner.download("https://youtube.com/watch?v=abc")

        self.assertEqual(path, "/tmp/video.webm")
        self.assertEqual(calls[0][0], "yt-dlp")
        self.assertIn("--write-auto-subs", calls[0])
        self.assertIn("--convert-subs", calls[0])

    def test_transcribe_uses_requested_model(self):
        module = load_module()
        seen = []

        def transcriber(path, model):
            seen.append((path, model))
            return "transcript"

        learner = module.MediaLearner(transcriber=transcriber)
        self.assertEqual(learner.transcribe("/tmp/video.webm", "small"), "transcript")
        self.assertEqual(seen, [("/tmp/video.webm", "small")])


if __name__ == "__main__":
    unittest.main()
