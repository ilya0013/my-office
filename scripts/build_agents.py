"""Собирает агентов из роли/*.md: .claude/agents/<name>.md и .codex/agents/<name>.toml.
Тело роли одно и то же в обеих программах. Роль без поля name (Босс) пропускается.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse(path):
    _, head, body = path.read_text(encoding="utf-8").split("---", 2)
    meta = dict(line.split(": ", 1) for line in head.strip().splitlines())
    return meta, body.strip()


def main():
    claude_dir = ROOT / ".claude" / "agents"
    codex_dir = ROOT / ".codex" / "agents"
    claude_dir.mkdir(parents=True, exist_ok=True)
    codex_dir.mkdir(parents=True, exist_ok=True)
    built = set()
    for path in sorted((ROOT / "роли").glob("*.md")):
        if path.name.startswith("_") or not path.read_text(encoding="utf-8").startswith("---"):
            continue  # шаблон и Босс — не сотрудники
        meta, body = parse(path)
        name = meta["name"]
        assert "'''" not in body, f"{path.name}: ''' ломает TOML"
        (claude_dir / f"{name}.md").write_bytes((  # байты: \n без замены на \r\n и на Python 3.9
            f"---\nname: {name}\ndescription: {meta['description']}\n"
            f"tools: {meta['claude_tools']}\nmodel: {meta['claude_model']}\n"
            + (f"effort: {meta['claude_effort']}\n" if "claude_effort" in meta else "")
            + f"omitClaudeMd: true\n---\n\n{body}\n").encode("utf-8"))
        description = meta["description"].replace("\\", "\\\\").replace('"', '\\"')
        (codex_dir / f"{name}.toml").write_bytes((
            f'name = "{name}"\ndescription = "{description}"\n'
            f'model = "{meta["codex_model"]}"\nmodel_reasoning_effort = "{meta["codex_effort"]}"\n'
            f"developer_instructions = '''\n{body}\n'''\n").encode("utf-8"))
        built.add(name)
        print(f"{path.name} -> {name}")
    # агенты от удалённых или переименованных ролей
    for f in [*claude_dir.glob("*.md"), *codex_dir.glob("*.toml")]:
        if f.stem not in built:
            f.unlink()
            print(f"удалён {f.name}: роли нет")


if __name__ == "__main__":
    main()
