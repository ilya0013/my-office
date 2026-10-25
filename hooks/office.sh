#!/usr/bin/env bash
# Хук «Моего офиса». Дописывает событие программы (JSON со stdin) в экран/events.js строкой ev({...});
# Экран офис.html перечитывает этот файл раз в 2 секунды.
# Папка-замок: параллельные сотрудники не перемешивают строки (одна битая строка гасит весь файл).
dir="$(cd "$(dirname "$0")/../экран" && pwd)"
line="ev($(cat), $(date +%s)000);"  # второй аргумент — время записи, мс
for _ in $(seq 40); do mkdir "$dir/.lock" 2>/dev/null && break; sleep 0.05; done
printf '%s\n' "$line" >> "$dir/events.js"
rmdir "$dir/.lock" 2>/dev/null
exit 0
