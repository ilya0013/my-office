#!/usr/bin/env bash
# Хук «Моего офиса». Дописывает событие программы (JSON со stdin) в экран/events.js строкой ev({...});
# Экран офис.html перечитывает этот файл раз в 2 секунды.
# Папка-замок: параллельные сотрудники не перемешивают строки (одна битая строка гасит весь файл).
dir="$(cd "$(dirname "$0")/../экран" && pwd)"
json="$(cat)"
line="ev($json, $(date +%s)000);"  # второй аргумент — время записи, мс
# Конец хода: статусы из файлов. Сотрудник мог менять их командой, которую экран не разберёт.
if printf '%s' "$json" | grep -Eq '"hook_event_name" *: *"(SubagentStop|Stop)"'; then
  letters=" $(cd "$dir/../письма" 2>/dev/null && ls -1 | tr '\n' ' ')"
  items="$(awk -v L="$letters" '
    function out() { if (n != "" && n !~ /^_/) printf "%s\"%s\":{\"статус\":\"%s\",\"компания\":\"%s\",\"письмо\":%s}", (k++ ? "," : ""), n, st, co, (index(L, " " n ".md ") ? "true" : "false") }
    FNR == 1 { out(); n = FILENAME; sub(/.*\//, "", n); sub(/\.md$/, "", n); st = ""; co = "" }
    { gsub(/[\r"\\]/, "") }
    /^статус:/ && st == "" { st = $0; sub(/^статус:[ \t]*/, "", st) }
    /^компания:/ && co == "" { co = $0; sub(/^компания:[ \t]*/, "", co) }
    END { out() }' "$dir"/../лиды/*.md 2>/dev/null)"
  line="$line
ev({\"hook_event_name\":\"MoFiles\",\"leads\":{$items}}, $(date +%s)000);"
fi
for _ in $(seq 40); do mkdir "$dir/.lock" 2>/dev/null && break; sleep 0.05; done
printf '%s\n' "$line" >> "$dir/events.js"
rmdir "$dir/.lock" 2>/dev/null
exit 0
