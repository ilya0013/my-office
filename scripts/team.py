"""Снимок команды и откат: python -I -X utf8 scripts/team.py save | restore [папка снимка].
save — копия ролей, правил, каталога, шаблона карточки и списка агентов в настройка/было/<время>/.
restore — сначала снимок того, что есть сейчас (<время>-до-отката: откат можно откатить, назвав
его), затем всё обратно из последнего неиспользованного (или названного) снимка; использованный
получает -возвращён, поэтому повторный restore идёт ещё на шаг назад. Роли, которых в снимке нет,
удаляются; затем сборка агентов.
"""
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAVED = ["роли", "ПРАВИЛА.md", "каталог.md", "лиды/_шаблон.md", "tests/test_build_agents.py"]
BACKUPS = ROOT / "настройка" / "было"


def save(suffix=""):
    stamp = time.strftime("%Y-%m-%d-%H%M%S") + suffix
    dest, n = BACKUPS / stamp, 1
    while dest.exists():
        n += 1
        dest = BACKUPS / f"{stamp}-{n}"
    for rel in SAVED:
        src, out = ROOT / rel, dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, out) if src.is_dir() else shutil.copy2(src, out)
    print(f"снимок: {dest.relative_to(ROOT)}")


def restore(name=None):
    used = ("до-отката", "возвращён")
    snaps = sorted(d for d in BACKUPS.glob("*") if (d / "роли").is_dir() and not d.name.endswith(used))         if BACKUPS.exists() else []
    src = BACKUPS / name if name else (snaps[-1] if snaps else None)
    if not src or not (src / "роли").is_dir():
        sys.exit("снимка команды нет")
    save("-до-отката")
    for rel in SAVED:
        if (ROOT / rel).is_dir():
            shutil.rmtree(ROOT / rel)
        if (src / rel).is_dir():
            shutil.copytree(src / rel, ROOT / rel)
        elif (src / rel).exists():
            shutil.copy2(src / rel, ROOT / rel)
    subprocess.run([sys.executable, "-I", "-X", "utf8", str(ROOT / "scripts" / "build_agents.py")], check=True)
    if not src.name.endswith(used):
        src = src.rename(src.with_name(src.name + "-возвращён"))
    print(f"вернул: {src.relative_to(ROOT)}")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("save", "restore"):
        sys.exit(__doc__)
    save() if sys.argv[1] == "save" else restore(*sys.argv[2:3])
