# То же, что office.sh, для Windows без bash. Файл сохранён с BOM: иначе PowerShell 5.1 читает кириллицу неверно.
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
$json = [Console]::In.ReadToEnd().Trim()
$dir = Join-Path (Split-Path $PSScriptRoot) 'экран'
$lock = Join-Path $dir '.lock'
for ($i = 0; $i -lt 40; $i++) { try { New-Item -ItemType Directory $lock -ErrorAction Stop | Out-Null; break } catch { Start-Sleep -Milliseconds 50 } }
[IO.File]::AppendAllText((Join-Path $dir 'events.js'), "ev($json, $([DateTimeOffset]::Now.ToUnixTimeMilliseconds()));`n", [Text.UTF8Encoding]::new($false))
Remove-Item $lock -ErrorAction SilentlyContinue
exit 0
