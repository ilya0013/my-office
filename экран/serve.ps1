# То же, что serve.py, для Windows без Python. Файл сохранён с BOM: иначе PowerShell 5.1 читает кириллицу неверно.
# Отдаёт папку проекта только на localhost, только чтение; корень — сразу экран.
# Сам выключается, если 10 минут нет запросов (открытый экран спрашивает раз в 2 с).
# Порт занят экраном другой папки офиса — сначала гасит его. Только погасить: serve.ps1 -Free.
param([int]$Port = 8765, [int]$IdleSeconds = 600, [switch]$Free)
function Stop-OldScreen {
  try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 -Headers @{ 'X-Office' = '1' } "http://localhost:$Port/__office-quit" | Out-Null; Start-Sleep 1 } catch { }
}
if ($Free) { Stop-OldScreen; exit 0 }
$root = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot)).TrimEnd([char]92) + [char]92   # с разделителем: соседняя «папкаX» не пройдёт
$types = @{ '.html' = 'text/html; charset=utf-8'; '.js' = 'text/javascript; charset=utf-8'; '.md' = 'text/plain; charset=utf-8';
  '.css' = 'text/css'; '.png' = 'image/png'; '.json' = 'application/json'; '.txt' = 'text/plain; charset=utf-8' }
$l = [Net.HttpListener]::new()
$l.Prefixes.Add("http://localhost:$Port/")
try { $l.Start() } catch {
  Stop-OldScreen
  $l = [Net.HttpListener]::new(); $l.Prefixes.Add("http://localhost:$Port/")
  try { $l.Start() } catch { Write-Error "Порт $Port занят другой программой — закройте её или скажите Управляющему «закончили» в другом офисе."; exit 1 }
}
while ($true) {
  $task = $l.GetContextAsync()
  if (-not $task.Wait($IdleSeconds * 1000)) { break }   # тишина — экран закрыт
  $c = $task.Result
  $r = $c.Response
  try {
    $rel = [Uri]::UnescapeDataString($c.Request.Url.AbsolutePath).TrimStart('/')
    if ($rel -eq '__office-quit' -and $c.Request.Headers['X-Office'] -eq '1') { $r.StatusCode = 204; break }   # ответ закроет finally; свой заголовок: чужая страница так не спросит
    if (-not $rel) { $r.Redirect('/' + [Uri]::EscapeUriString('экран/офис.html')); continue }
    if ($rel -match '(^|[\\/])\.') { $r.StatusCode = 404; continue }   # .git, .claude, .env — не отдаём
    $f = [IO.Path]::GetFullPath((Join-Path $root $rel))
    if (-not $f.StartsWith($root, [StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $f -PathType Leaf)) { $r.StatusCode = 404; continue }
    $b = [IO.File]::ReadAllBytes($f)
    $t = $types[[IO.Path]::GetExtension($f).ToLower()]
    $r.ContentType = if ($t) { $t } else { 'application/octet-stream' }
    $r.Headers.Add('Cache-Control', 'no-store')   # события перечитываются раз в 2 с
    $r.OutputStream.Write($b, 0, $b.Length)
  } catch { $r.StatusCode = 500 } finally { $r.Close() }
}
$l.Stop()
