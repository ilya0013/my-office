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
  # Вкладка «База»: шапки компаний и письма целиком — в решения.js, файл переписывается (events.js не растёт)
  $dec = [ordered]@{}
  foreach ($f in Get-ChildItem (Join-Path $root 'лиды') -Filter *.md -ErrorAction SilentlyContinue) {
    if ($f.BaseName.StartsWith('_')) { continue }
    $d = [ordered]@{}; $fm = 0
    foreach ($l in [IO.File]::ReadAllLines($f.FullName, [Text.UTF8Encoding]::new($false))) {
      if ($l -match '^---') { if (++$fm -gt 1) { break }; continue }
      if ($fm -eq 1 -and $l -match '^(компания|статус|сайт|почему|город|контакт|проба):\s*(.*)$' -and -not $d.Contains($Matches[1])) { $d[$Matches[1]] = $Matches[2].Trim() }
    }
    $p = Join-Path $root "письма\$($f.Name)"
    if (Test-Path $p) {
      $sec = ''
      foreach ($l in [IO.File]::ReadAllLines($p, [Text.UTF8Encoding]::new($false))) {
        if ($l -match '^Кому:' -and -not $d.Contains('кому')) { $k, $t = $l -split ' · Тема:', 2; $d['кому'] = ($k -replace '^Кому:\s*', '').Trim(); if ($t) { $d['тема'] = $t.Trim() }; continue }
        if ($l -match '^Проверка:\s*(.*)$' -and -not $d.Contains('проверка')) { $d['проверка'] = $Matches[1].Trim(); continue }
        if ($l -match '^## ') { $sec = if ($l -match '^## Письмо') { 'письмо' } elseif ($l -match '^## Перевод') { 'перевод' } else { '' }; continue }
        if ($sec) { $d[$sec] += "$l`n" }
      }
    }
    $dec[$f.BaseName] = $d
  }
  $tmp = Join-Path $dir "решения.$PID.tmp"
  [IO.File]::WriteAllText($tmp, "dec($($dec | ConvertTo-Json -Compress -Depth 4));`n", [Text.UTF8Encoding]::new($false))
  Move-Item $tmp (Join-Path $dir 'решения.js') -Force
}
$lock = Join-Path $dir '.lock'
for ($i = 0; $i -lt 40; $i++) { try { New-Item -ItemType Directory $lock -ErrorAction Stop | Out-Null; break } catch { Start-Sleep -Milliseconds 50 } }
[IO.File]::AppendAllText((Join-Path $dir 'events.js'), $line, [Text.UTF8Encoding]::new($false))
Remove-Item $lock -ErrorAction SilentlyContinue
exit 0
