"""Сборка ролей: из роли/*.md получаются агенты Claude Code и Codex.
Запуск: python -m unittest discover tests
"""
import subprocess
import sys
import unittest
try:
    import tomllib
except ImportError:  # Python 3.9–3.10: на Mac Python от Apple — 3.9
    tomllib = None
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKERS = ["scout", "manager", "checker"]


def frontmatter(path):
    head = path.read_text(encoding="utf-8").split("---")[1]
    return dict(line.split(": ", 1) for line in head.strip().splitlines())


def codex(name):
    return tomllib.loads((ROOT / ".codex" / "agents" / f"{name}.toml").read_text(encoding="utf-8"))


class BuildAgents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "build_agents.py")], check=True)

    def test_claude_effort(self):
        roles = [frontmatter(p) for p in (ROOT / "роли").glob("[!_]*.md")
                 if p.read_text(encoding="utf-8").startswith("---")]
        for role in roles:
            meta = frontmatter(ROOT / ".claude" / "agents" / f"{role['name']}.md")
            self.assertEqual(meta.get("effort"), role.get("claude_effort"))

    def test_claude_agents(self):
        for name in WORKERS:
            meta = frontmatter(ROOT / ".claude" / "agents" / f"{name}.md")
            self.assertEqual(meta["name"], name)
            self.assertIn(meta["model"], {"haiku", "sonnet"})
            self.assertNotIn("Bash", meta["tools"])  # отправлять наружу нечем

    @unittest.skipIf(tomllib is None, "агенты Codex не проверены: нужен Python 3.11+")
    def test_codex_agents(self):
        for name in WORKERS:
            agent = codex(name)
            self.assertEqual(agent["name"], name)
            self.assertTrue(agent["model"].startswith("gpt-"))
            self.assertIn("ПРАВИЛА.md", agent["developer_instructions"])

    def test_stale_agents_removed(self):
        stale = [ROOT / ".claude" / "agents" / "old-role.md", ROOT / ".codex" / "agents" / "old-role.toml"]
        for f in stale:
            f.write_text("x", encoding="utf-8")
        subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "build_agents.py")], check=True,
                       capture_output=True)
        for f in stale:
            self.assertFalse(f.exists(), f"{f.name}: агент без роли остался")

    @unittest.skipIf(tomllib is None, "агенты Codex не проверены: нужен Python 3.11+")
    def test_same_instructions_in_both(self):
        for name in WORKERS:
            text = (ROOT / ".claude" / "agents" / f"{name}.md").read_text(encoding="utf-8")
            self.assertEqual(text.split("---", 2)[2].strip(), codex(name)["developer_instructions"].strip())


if __name__ == "__main__":
    unittest.main()
