#!/usr/bin/env bash
# Хук «Моего офиса». Дописывает событие программы (JSON со stdin) в экран/events.js строкой ev({...});
# Экран офис.html перечитывает этот файл раз в 2 секунды.
# Папка-замок: параллельные сотрудники не перемешивают строки (одна битая строка гасит весь файл).
dir="$(cd "$(dirname "$0")/../экран" && pwd)"
json="$(cat)"
shopt -s nullglob   # нет писем — «письма/*.md» исчезает, а не уходит в awk строкой (awk бы упал, «База» пустая)
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
  # Вкладка «База»: шапки компаний и письма целиком — в решения.js, файл переписывается (events.js не растёт)
  dec="$(awk '
    function js(s,  o, i, c) { o = ""; for (i = 1; i <= length(s); i++) { c = substr(s, i, 1); o = o (c == "\\" || c == "\"" ? "\\" c : c == "\t" ? " " : c) } return o }
    function val(s) { sub(/^[^:]*:[ \t]*/, "", s); return js(s) }
    FNR == 1 { L = FILENAME ~ /письма\/[^\/]*$/; n = FILENAME; sub(/.*\//, "", n); sub(/\.md$/, "", n); fm = 0; sec = ""
      if (!L && n !~ /^_/) { seen[n] = 1; order[++k] = n } }
    { sub(/\r$/, "") }
    !(n in seen) { next }
    !L && /^---/ { fm++; next }
    !L && fm == 1 && /^(компания|статус|сайт|почему|город|контакт):/ { key = $0; sub(/:.*/, "", key); if (!((n, key) in f)) f[n, key] = val($0); next }
    L && /^Кому:/ && !((n, "кому") in f) { t = $0; i = index(t, " · Тема:"); f[n, "тема"] = i ? val(substr(t, i)) : ""; f[n, "кому"] = val(i ? substr(t, 1, i - 1) : t); next }
    L && /^Проверка:/ && !((n, "проверка") in f) { f[n, "проверка"] = val($0); next }
    L && /^## / { sec = $0 ~ /^## Письмо/ ? "письмо" : $0 ~ /^## Перевод/ ? "перевод" : ""; next }
    L && sec != "" { f[n, sec] = f[n, sec] js($0) "\\n" }
    END { split("компания статус сайт почему город контакт кому тема проверка письмо перевод", K, " ")
      for (j = 1; j <= k; j++) { n = order[j]; s = ""
        for (m = 1; m <= 11; m++) if ((n, K[m]) in f) s = s (s == "" ? "" : ",") "\"" K[m] "\":\"" f[n, K[m]] "\""
        printf "%s\"%s\":{%s}", (j > 1 ? "," : ""), n, s } }' "$dir"/../лиды/*.md "$dir"/../письма/*.md 2>/dev/null)"
  printf 'dec({%s});\n' "$dec" > "$dir/решения.$$.tmp" && mv -f "$dir/решения.$$.tmp" "$dir/решения.js"
fi
for _ in $(seq 40); do mkdir "$dir/.lock" 2>/dev/null && break; sleep 0.05; done
printf '%s\n' "$line" >> "$dir/events.js"
rmdir "$dir/.lock" 2>/dev/null
exit 0
