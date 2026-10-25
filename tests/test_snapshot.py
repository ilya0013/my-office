"""Снимок команды и «верни команду как было»: лишняя роль и её агенты исчезают.
Запуск: python -m unittest discover tests
"""
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Snapshot(unittest.TestCase):
    def test_restore_removes_hired_role(self):
        with tempfile.TemporaryDirectory() as tmp:
            office = Path(tmp)
            for d in ("роли", "scripts", "tests"):
                shutil.copytree(ROOT / d, office / d, ignore=shutil.ignore_patterns("__pycache__"))
            for f in ("ПРАВИЛА.md", "каталог.md"):
                shutil.copy(ROOT / f, office / f)
            (office / "лиды").mkdir()
            shutil.copy(ROOT / "лиды" / "_шаблон.md", office / "лиды" / "_шаблон.md")
            py = lambda *a: subprocess.run([sys.executable, "-I", "-X", "utf8", *a], cwd=office, check=True,
                                           capture_output=True, text=True, encoding="utf-8")
            py("scripts/build_agents.py")
            py("scripts/team.py", "save")
            hired = (ROOT / "роли" / "менеджер.md").read_text(encoding="utf-8").replace("name: manager", "name: hired")
            (office / "роли" / "нанятый.md").write_text(hired, encoding="utf-8")
            (office / "каталог.md").write_text("изменён", encoding="utf-8")
            py("scripts/build_agents.py")
            self.assertTrue((office / ".claude" / "agents" / "hired.md").exists())
            py("scripts/team.py", "restore")
            self.assertFalse((office / "роли" / "нанятый.md").exists())
            self.assertFalse((office / ".claude" / "agents" / "hired.md").exists())
            self.assertFalse((office / ".codex" / "agents" / "hired.toml").exists())
            self.assertEqual((office / "каталог.md").read_text(encoding="utf-8"), text(ROOT / "каталог.md"))
            # откат сам сохранил то, что было до него: поздние правки каталога не пропали
            snaps = sorted((office / "настройка" / "было").glob("*/каталог.md"))
            self.assertEqual(len(snaps), 2)
            self.assertEqual(text(snaps[-1]), "изменён")


def text(p):
    return p.read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
