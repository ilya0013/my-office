"""Собирает ZIP «Моего офиса» из закоммиченных файлов и отказывает, если что-то не так.

Запуск: python scripts/release.py <версия> <папка для ZIP>
Кладёт два одинаковых архива: my-office-v<версия>.zip и my-office.zip — для постоянной ссылки
releases/latest/download/my-office.zip. Внутри архива всё лежит в папке my-office/.
"""
import json
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_ONLY = ("docs/сценарий-2ч.md", "docs/лаба.md", "scripts/release.py", "scripts/screen/")  # для ведущего и сборки
NO_SCAN = ("scripts/screen/cubicle-0.38.1.html", "scripts/release.py")  # оригинал Cubicle; сам список проверок
PERSONAL = [Path.home().name, "C:\\Users", "C:/Users"]  # следы машины, где собирают выпуск
MUST = ["README.md", "INSTALL.md", "LICENSE", "CLAUDE.md", "AGENTS.md", "ПРАВИЛА.md", "каталог.md",
        ".claude/settings.json", ".codex/config.toml", ".codex/hooks.json",
        "экран/офис.html", "hooks/office.sh", "hooks/office.ps1", "экран/demo-events.js",
        "экран/LICENSE-cubicle.txt", "лиды/_шаблон.md", "входящие.md",
        "экран/serve.py", "экран/serve.ps1", ".claude/launch.json",   # экран во встроенном браузере Claude Code
        # на них ссылаются роли, README и scripts/trial.py
        "docs/перестроить-офис.md", "docs/под-своё-дело.md", "docs/почему-команда.md", "docs/модели.md",
        "docs/испытание-codex.md", "docs/отправка-писем.md", "scripts/trial.py", "tests/test_build_agents.py"]


def fail(msg):
    sys.exit(f"ОТКАЗ: {msg}")


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), "-c", "core.quotepath=false", *args],
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 3:
        fail("python scripts/release.py <версия> <папка для ZIP>")
    version, outdir = sys.argv[1], Path(sys.argv[2])
    if git("status", "--porcelain").strip():
        fail("есть незакоммиченные изменения")
    tracked = git("ls-files").splitlines()
    files = sorted(f for f in tracked if not f.startswith(REPO_ONLY))
    missing = [f for f in MUST if f not in files]
    if missing:
        fail(f"нет файлов: {missing}")

    subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / "build_agents.py")], check=True,
                   capture_output=True)
    if git("status", "--porcelain").strip():
        fail("агенты в .claude/.codex не совпадают с роли/ — пересобери и закоммить")

    json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
    json.loads((ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
    tomllib.loads((ROOT / ".codex/config.toml").read_text(encoding="utf-8"))
    for f in (t for t in tracked if t not in NO_SCAN):  # весь репозиторий публичный, не только архив
        raw = (ROOT / f).read_bytes()
        if b"\r\n" in raw:
            fail(f"{f}: CRLF вместо LF")
        text = raw.decode("utf-8", errors="ignore")
        hits = [w for w in PERSONAL if w.lower() in text.lower()]
        if hits:
            fail(f"{f}: следы авторской среды {hits}")
    for f in ("README.md", "INSTALL.md"):
        if f"v{version}" not in (ROOT / f).read_text(encoding="utf-8"):
            fail(f"{f} не называет версию v{version}")

    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"my-office-v{version}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(ROOT / f, f"my-office/{f}")
    names = zipfile.ZipFile(out).namelist()
    if [n.removeprefix("my-office/") for n in names] != files:
        fail("состав собранного ZIP не совпал")
    (outdir / "my-office.zip").write_bytes(out.read_bytes())
    print(f"OK: {out.name} (+ my-office.zip), {len(files)} файлов, {out.stat().st_size} байт")


if __name__ == "__main__":
    main()
