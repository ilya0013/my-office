"""Мастер настройки: настройки живут в каталоге, роли читают их оттуда, проба видна на экране.
Запуск: python -m unittest discover tests
"""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LETTER, CHECK = "## Каким должно быть письмо", "## Что проверяем"


def text(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class Settings(unittest.TestCase):
    def test_catalog_has_letter_and_check(self):
        for section in (LETTER, CHECK):
            self.assertIn(section, text("каталог.md"))

    def test_roles_read_settings_from_catalog(self):
        self.assertIn(LETTER[3:], text("роли/менеджер.md"))
        self.assertIn(CHECK[3:], text("роли/проверяющий.md"))

    def test_boss_setup_mode(self):
        boss = text("роли/босс.md")
        for must in ("## Настройка", "настройка/было/", "проба: да", "верни как было", "Статус: настраивается"):
            self.assertIn(must, boss)

    def test_boss_team_mode(self):
        boss = text("роли/босс.md")
        for must in ("## Команда", "build_agents.py", "новый чат"):
            self.assertIn(must, boss)


class ProbeOnScreen(unittest.TestCase):
    """Хук отдаёт экрану строку «проба: да» из шапки компании — «База» помечает пробу."""

    def run_hook(self, cmd, name):
        with tempfile.TemporaryDirectory() as tmp:
            office = Path(tmp)
            shutil.copytree(ROOT / "hooks", office / "hooks")
            for sub in ("лиды", "письма", "экран"):
                (office / sub).mkdir()
            (office / "лиды" / "alpik.md").write_text(
                "---\nкомпания: Alpík\nстатус: проверено\nпроба: да\n---\n", encoding="utf-8")
            subprocess.run([*cmd, str(office / "hooks" / name)], input='{"hook_event_name":"Stop"}',
                           text=True, encoding="utf-8", check=True, capture_output=True)
            dec = (office / "экран" / "решения.js").read_text(encoding="utf-8")
            return json.loads(dec.strip()[len("dec("):-len(");")])

    def test_bash_hook(self):
        if not shutil.which("bash"):
            self.skipTest("нет bash")
        self.assertEqual(self.run_hook(["bash"], "office.sh")["alpik"].get("проба"), "да")

    def test_powershell_hook(self):
        ps = shutil.which("powershell")
        if not ps:
            self.skipTest("нет Windows PowerShell")
        self.assertEqual(self.run_hook([ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File"], "office.ps1")
                         ["alpik"].get("проба"), "да")


if __name__ == "__main__":
    unittest.main()
