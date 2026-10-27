"""Снимок команды и «верни команду как было»: лишняя роль и её агенты исчезают, повторный откат
идёт дальше назад, а то, что было до отката, сохраняется снимком «до-отката».
Запуск: python -m unittest discover tests
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def text(p):
    return p.read_text(encoding="utf-8")


class Snapshot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.office = office = Path(self.tmp.name)
        for d in ("роли", "scripts", "tests"):
            shutil.copytree(ROOT / d, office / d, ignore=shutil.ignore_patterns("__pycache__"))
        for f in ("ПРАВИЛА.md", "каталог.md"):
            shutil.copy(ROOT / f, office / f)
        (office / "лиды").mkdir()
        shutil.copy(ROOT / "лиды" / "_шаблон.md", office / "лиды" / "_шаблон.md")
        self.py("scripts/build_agents.py")
        # образец роли сотрудника — любая роль с шапкой (после перестройки аналитика может не быть)
        self.sample = next(text(p) for p in sorted((office / "роли").glob("[!_]*.md")) if text(p).startswith("---"))

    def tearDown(self):
        self.tmp.cleanup()

    def py(self, *a):
        return subprocess.run([sys.executable, "-I", "-X", "utf8", *a], cwd=self.office, check=True,
                              capture_output=True, text=True, encoding="utf-8")

    def hire(self, name):
        self.py("scripts/team.py", "save")
        head, body = self.sample.split("\n", 2)[1], self.sample
        (self.office / "роли" / f"{name}.md").write_text(body.replace(head, f"name: {name}", 1), encoding="utf-8")
        self.py("scripts/build_agents.py")

    def agent(self, name):
        return (self.office / ".claude" / "agents" / f"{name}.md").exists()

    def test_restore_twice_goes_further_back(self):
        catalog = text(self.office / "каталог.md")
        self.hire("first")
        self.hire("second")
        (self.office / "каталог.md").write_text("изменён", encoding="utf-8")
        self.py("scripts/team.py", "restore")
        self.assertTrue(self.agent("first"))
        self.assertFalse(self.agent("second"))
        self.assertFalse((self.office / ".codex" / "agents" / "second.toml").exists())
        self.py("scripts/team.py", "restore")
        self.assertFalse(self.agent("first"))
        self.assertFalse((self.office / "роли" / "first.md").exists())
        self.assertEqual(text(self.office / "каталог.md"), catalog)
        # поздние правки каталога не пропали: лежат в снимке «до-отката»
        saved = (self.office / "настройка" / "было").glob("*до-отката/каталог.md")
        self.assertIn("изменён", [text(s) for s in saved])  # порядок в одну секунду не важен


if __name__ == "__main__":
    unittest.main()
