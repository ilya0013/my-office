"""Испытание офиса перед работой: офис и один чат делают одну задачу на N объектах,
независимый проверяющий вслепую открывает ссылки, отчёт — docs/испытание.md.
Запуск (Claude Code): python -I -X utf8 scripts/trial.py 3
Тратит лимит подписки: примерно как три обычные партии.
"""
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE = shutil.which("claude")
TOOLS = ["WebSearch", "WebFetch", "Read", "Write", "Edit", "Glob", "Grep", "Agent", "Task"]
SKIP = {".git", "лиды", "письма", "ответы", "настройка", "входящие.md", "events.js", "испытание.md", "моя-задача.md"}

OFFICE = "Знакомство пропусти. Работаем по каталогу. Найди {n}. Сразу письма, без остановки на списке, ничего не спрашивай."
CHAT = ("В каталог.md — кто мы, зачем работаем и что предлагаем. Сделай ту же работу одним чатом "
        "для {n} объектов: найди их, проверь по их сайтам, результат по каждому — файл письма/<имя>.md. "
        "Ничего никуда не отправляй.")
CHECK = ("Ты — независимый проверяющий. Ничего не меняй и не отправляй. Прочитай каталог.md. Для каждого "
         "файла в письма/ выпиши до 3 главных утверждений о внешнем объекте (что у них есть, чего нет, цены, "
         "контакт), открой ссылки и проверь: подтвердилось, неверно или не проверить. Утверждения о наших "
         "товарах сверяй с каталогом. Вердикт на файл: «как есть», «правка» или «не отправлять». "
         "Последней строкой ответа напиши ровно: ИТОГ: как есть=<число> правка=<число> "
         "не отправлять=<число> неверных=<число>")


def run(prompt, cwd):
    t0 = time.time()
    model = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")).get("model", "sonnet")
    r = subprocess.run([CLAUDE, "-p", "--model", model, "--output-format", "json", "--permission-mode", "acceptEdits",
                        "--allowedTools", *TOOLS], cwd=cwd, input=prompt, capture_output=True,
                       text=True, encoding="utf-8")
    d = json.loads(r.stdout or "{}")
    return {"мин": round((time.time() - t0) / 60, 1), "$": round(d.get("total_cost_usd") or 0, 2),
            "ответ": d.get("result", "")}


def check(cwd):
    out = run(CHECK, cwd)
    m = re.search(r"ИТОГ: как есть=(\d+) правка=(\d+) не отправлять=(\d+) неверных=(\d+)", out["ответ"])
    out["итог"] = dict(zip(["как есть", "правка", "не отправлять", "неверных"], map(int, m.groups()))) if m else {}
    return out


def main():
    if not CLAUDE:
        sys.exit("Команда claude не найдена: испытанию нужен Claude Code в терминале (не только приложение).")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    base = ROOT.parent / f"{ROOT.name}-испытание-{time.strftime('%Y-%m-%d-%H%M')}"  # повтор не смешивается с прошлым
    office, chat = base / "офис", base / "один-чат"
    shutil.copytree(ROOT, office, ignore=lambda d, names: [x for x in names if x in SKIP], dirs_exist_ok=True)
    for sub in ("лиды", "письма", "ответы"):
        (office / sub).mkdir(exist_ok=True)
    shutil.copy(ROOT / "лиды" / "_шаблон.md", office / "лиды" / "_шаблон.md")
    (office / "экран" / "events.js").write_text("", encoding="utf-8")
    (chat / "письма").mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "каталог.md", chat / "каталог.md")

    print(f"Испытание на {n}: офис и один чат в {base} — 15–40 минут.", flush=True)
    res = {"Офис": run(OFFICE.format(n=n), office), "Один чат": run(CHAT.format(n=n), chat)}
    for name, cwd in (("Офис", office), ("Один чат", chat)):
        res[name]["результатов"] = len(list((cwd / "письма").glob("*.md")))
        res[name]["проверка"] = check(cwd)

    rows = []
    for name, r in res.items():
        it, ok = r["проверка"]["итог"], r["проверка"]["итог"].get("как есть", 0)
        per = f"{r['$'] / ok:.2f}" if ok else "—"
        rows.append(f"| {name} | {r['мин']} | {r['$']} | {r['результатов']} | {ok} | {it.get('правка', '?')} | "
                    f"{it.get('не отправлять', '?')} | {it.get('неверных', '?')} | {per} |")
    o, c = res["Офис"]["проверка"]["итог"], res["Один чат"]["проверка"]["итог"]
    if not o:
        verdict = "Проверка офиса не дала итога — посмотрите её ответ ниже и повторите испытание."
    elif o.get("неверных", 1) == 0 and o.get("не отправлять", 1) == 0 and o.get("как есть", 0) >= max(1, n // 2):
        verdict = "Офис готов к работе: неверных фактов нет, большинство результатов можно отправлять как есть."
    else:
        verdict = "Офис пока не готов: поправьте роли по замечаниям проверки и повторите испытание."
    if o and c and c.get("неверных", 0) == 0 and c.get("как есть", 0) >= o.get("как есть", 0):
        verdict += " Один чат справился не хуже — для этой задачи команда может быть не нужна."
    report = (f"# Испытание офиса — {date.today()}\n\nОбъектов в задаче: {n}. Офис и один чат делали одно и то же, "
              "результаты вслепую проверил отдельный агент: открыл ссылки и сверил факты.\n\n"
              "| | Мин | $ | Результатов | Как есть | Правка | Не отправлять | Неверных фактов | $ за результат «как есть» |\n"
              "|---|---|---|---|---|---|---|---|---|\n" + "\n".join(rows) +
              f"\n\n**Вердикт:** {verdict}\n\nПапки испытания: `{base}`.\n\n"
              f"## Проверка офиса\n{res['Офис']['проверка']['ответ']}\n\n"
              f"## Проверка одного чата\n{res['Один чат']['проверка']['ответ']}\n")
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "испытание.md").write_bytes(report.encode("utf-8"))  # \n как есть и на Python 3.9
    print(verdict, "\nОтчёт: docs/испытание.md")


if __name__ == "__main__":
    main()
