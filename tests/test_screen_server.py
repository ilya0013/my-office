"""Сервер экрана: второй офис на том же порту гасит экран первого и показывает свой.
Запуск: python -m unittest discover tests
"""
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def office(base, name):
    d = base / name / "экран"
    d.mkdir(parents=True)
    shutil.copy(ROOT / "экран" / "serve.py", d)
    shutil.copy(ROOT / "экран" / "serve.ps1", d)
    (d / "events.js").write_text(f"// {name}\n", encoding="utf-8")
    return d


def shows(port, name):
    """Экран на порту за 10 с стал экраном офиса name."""
    url = f"http://localhost:{port}/{urllib.parse.quote('экран')}/events.js"
    for _ in range(50):
        try:
            if name in urllib.request.urlopen(url, timeout=1).read().decode("utf-8"):
                return True
        except OSError:
            pass
        time.sleep(0.2)
    return False


class TakeOver(unittest.TestCase):
    def take_over(self, cmd):
        port = free_port()
        with tempfile.TemporaryDirectory() as tmp:
            a, b = office(Path(tmp), "первый"), office(Path(tmp), "второй")
            pa = subprocess.Popen(cmd(a, port), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                self.assertTrue(shows(port, "первый"))
                pb = subprocess.Popen(cmd(b, port), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    self.assertTrue(shows(port, "второй"), "порт остался у первого офиса")
                    self.assertIsNotNone(pa.wait(timeout=10), "экран первого офиса не погас")
                finally:
                    pb.kill(); pb.wait()
            finally:
                pa.kill(); pa.wait()

    def test_python_server(self):
        self.take_over(lambda d, port: [sys.executable, "-I", "-X", "utf8", str(d / "serve.py"), str(port)])

    def test_powershell_server(self):
        ps = shutil.which("powershell")
        if not ps:
            self.skipTest("нет Windows PowerShell")
        self.take_over(lambda d, port: [ps, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(d / "serve.ps1"), "-Port", str(port)])


if __name__ == "__main__":
    unittest.main()
