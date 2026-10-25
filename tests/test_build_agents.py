"""Сборка ролей: из роли/*.md получаются агенты Claude Code и Codex.
Запуск: python -m unittest discover tests
"""
import re
import subprocess
import sys
import unittest
try:
    import tomllib
except ImportError:  # Python 3.9–3.10: на Mac Python от Apple — 3.9
    tomllib = None
from pathlib import Path

# Ровно то, что пишет build_agents.py: строки key = "..." и в конце developer_instructions = '''...'''.
# Всё, что не так, — ошибка. Мягче tomllib только там, что сборка и так не пишет: ''' в теле, повтор ключа.
CODEX_TOML = re.compile(r"((?:\w+ = \"(?:[^\"\\\n]|\\[\"\\])*\"\n)+)developer_instructions = '''\n(.*)'''\n", re.S)

ROOT = Path(__file__).resolve().parent.parent
WORKERS = ["scout", "manager", "checker"]


def frontmatter(path):
    head = path.read_text(encoding="utf-8").split("---")[1]
    return dict(line.split(": ", 1) for line in head.strip().splitlines())


def codex(name):
    text = (ROOT / ".codex" / "agents" / f"{name}.toml").read_text(encoding="utf-8")
    if tomllib:
        return tomllib.loads(text)
    m = CODEX_TOML.fullmatch(text)
    assert m, f"{name}.toml: не тот формат, Codex его не прочтёт"
    agent = {k: re.sub(r"\\(.)", r"\1", v) for k, v in re.findall(r'(\w+) = "(.*)"', m[1])}
    return {**agent, "developer_instructions": m[2]}


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

    def test_same_instructions_in_both(self):
        for name in WORKERS:
            text = (ROOT / ".claude" / "agents" / f"{name}.md").read_text(encoding="utf-8")
            self.assertEqual(text.split("---", 2)[2].strip(), codex(name)["developer_instructions"].strip())


if __name__ == "__main__":
    unittest.main()
