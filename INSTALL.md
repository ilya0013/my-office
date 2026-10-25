# Установка «Мой офис» v0.2.0

Для агента, который ставит офис по ссылке. Владельцу читать не обязательно.

1. Папка должна быть пустой или содержать только служебные файлы программы. Есть чужие файлы —
   ничего не перезаписывай, покажи совпадения и спроси.
2. Скачай `https://github.com/ilya0013/my-office/releases/latest/download/my-office.zip` во
   временную папку, распакуй **`tar -xf my-office.zip`** (есть в Windows 10/11 и на Mac; в Git Bash `tar` другой и
   zip не читает — там `"$SYSTEMROOT/System32/tar.exe" -xf my-office.zip`; `unzip` портит русские имена) и перенеси **содержимое** папки `my-office` сюда, включая файлы
   с точкой (`.claude`, `.codex`, `.gitattributes`, `.gitignore`). В bash/zsh: `cp -R <папка>/. .`;
   в PowerShell: `Copy-Item <папка>\* . -Recurse -Force` и отдельно `<папка>\.*`.
3. Проверь, что на месте: `CLAUDE.md`, `AGENTS.md`, `ПРАВИЛА.md`, `каталог.md`, `входящие.md`,
   `роли/` (5 файлов: `босс.md`, `разведчик.md`, `менеджер.md`, `проверяющий.md`, `_шаблон-роли.md`),
   `.claude/agents/` и `.codex/agents/` (по 3 файла: scout, manager, checker), `.claude/settings.json`, `.codex/hooks.json`,
   `hooks/office.sh` и `hooks/office.ps1`, `экран/офис.html`, `лиды/_шаблон.md`. Русские имена файлов должны читаться — если видишь
   «╨Я╨а…», распакуй заново другим способом (PowerShell `Expand-Archive`, на Mac `ditto -x -k`).
4. Создай пустой файл `экран/events.js` своим инструментом записи файлов (не `>` и не `Out-File`
   в PowerShell: они пишут UTF-16, и экран его не прочтёт). В него хуки пишут события для экрана.
5. **Только Claude Code на Windows без Git Bash** (у тебя нет инструмента Bash, только PowerShell):
   в `.claude/settings.json` в каждом из пяти хуков (`UserPromptSubmit`, `PreToolUse`,
   `SubagentStart`, `SubagentStop`, `Stop`) замени два поля, символ в символ:
   ```json
   "shell": "powershell",
   "command": "powershell -NoProfile -ExecutionPolicy Bypass -File \"$env:CLAUDE_PROJECT_DIR\\hooks\\office.ps1\""
   ```
   После правки проверь, что файл читается как JSON. Иначе экран останется пустым, а при битом
   JSON пропадут и разрешения на поиск.
6. Временные файлы удали. Глобальные настройки программы не меняй.
7. Отчёт владельцу — 4 строки:
   - «Офис установлен.»
   - «Откройте `экран/офис.html` двойным щелчком — это ваш офис, держите его рядом с чатом.»
   - «Начните **новый чат** в этой папке — сотрудники подключаются при старте чата.»
   - Codex: «В новом чате Codex покажет окно „Проверка хуков" — нажмите „Разрешить все",
     без этого экран не видит сотрудников.»
