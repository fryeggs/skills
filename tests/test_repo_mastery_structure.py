import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL = ROOT / "repo-mastery" / "SKILL.md"
README = ROOT / "README.md"


class RepoMasteryStructureTest(unittest.TestCase):
    def test_skill_exists_with_required_metadata(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("name: repo-mastery", text)
        self.assertIn("description: Use when", text)

    def test_defaults_to_target_feature_driven_learning(self):
        text = SKILL.read_text(encoding="utf-8").lower()
        self.assertIn("target-feature-driven", text)
        self.assertIn("requested feature", text)

    def test_requires_safety_and_completion_evidence(self):
        text = SKILL.read_text(encoding="utf-8").lower()
        self.assertIn("license", text)
        self.assertIn("worktree", text)
        self.assertIn("verification evidence", text)

    def test_legacy_public_skills_are_absent(self):
        for name in ("chatgpt-web", "team-tasks"):
            self.assertFalse((ROOT / name).exists(), name)

    def test_readme_has_no_removed_skill_entries(self):
        text = README.read_text(encoding="utf-8").lower()
        for name in ("chatgpt-web", "opencli", "cli-anything", "team-tasks"):
            self.assertNotIn(name, text)


if __name__ == "__main__":
    unittest.main()
