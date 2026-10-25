# То же, что office.sh, для Windows без bash. Файл сохранён с BOM: иначе PowerShell 5.1 читает кириллицу неверно.
[Console]::InputEncoding = [Text.UTF8Encoding]::new($false)
$json = [Console]::In.ReadToEnd().Trim()
$dir = Join-Path (Split-Path $PSScriptRoot) 'экран'
$line = "ev($json, $([DateTimeOffset]::Now.ToUnixTimeMilliseconds()));`n"
# Конец хода: статусы из файлов. Сотрудник мог менять их командой, которую экран не разберёт.
if ($json -match '"hook_event_name"\s*:\s*"(SubagentStop|Stop)"') {
  $root = Split-Path $PSScriptRoot
  $leads = [ordered]@{}
  foreach ($f in Get-ChildItem (Join-Path $root 'лиды') -Filter *.md -ErrorAction SilentlyContinue) {
    if ($f.BaseName.StartsWith('_')) { continue }
    $text = [IO.File]::ReadAllLines($f.FullName, [Text.UTF8Encoding]::new($false))
    $st = ($text | Where-Object { $_ -match '^статус:' } | Select-Object -First 1) -replace '^статус:\s*', ''
    $co = ($text | Where-Object { $_ -match '^компания:' } | Select-Object -First 1) -replace '^компания:\s*', ''
    $leads[$f.BaseName] = [ordered]@{ 'статус' = "$st".Trim(); 'компания' = "$co".Trim(); 'письмо' = (Test-Path (Join-Path $root "письма\$($f.Name)")) }
  }
  $snap = [ordered]@{ hook_event_name = 'MoFiles'; leads = $leads } | ConvertTo-Json -Compress -Depth 4
  $line += "ev($snap, $([DateTimeOffset]::Now.ToUnixTimeMilliseconds()));`n"
}
$lock = Join-Path $dir '.lock'
for ($i = 0; $i -lt 40; $i++) { try { New-Item -ItemType Directory $lock -ErrorAction Stop | Out-Null; break } catch { Start-Sleep -Milliseconds 50 } }
[IO.File]::AppendAllText((Join-Path $dir 'events.js'), $line, [Text.UTF8Encoding]::new($false))
Remove-Item $lock -ErrorAction SilentlyContinue
exit 0
