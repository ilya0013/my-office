"""Экран «Мой офис» для встроенного браузера Claude Code: он показывает файл без соседних
events.js и решения.js, поэтому экран отдаётся с localhost. Только чтение, только эта машина.
Сам выключается, если 10 минут нет запросов (открытый экран спрашивает раз в 2 с).
Запуск: python3 экран/serve.py [порт] — откройте http://localhost:<порт>/
Порт занят экраном другой папки офиса — сначала гасит его. Только погасить: serve.py --free [порт].
"""
import functools, http.server, os, pathlib, sys, threading, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]   # папка проекта: экран ссылается на ../лиды и ../письма
FREE = '--free' in sys.argv
ARGS = [a for a in sys.argv[1:] if a != '--free']
PORT = int(ARGS[0]) if ARGS else 8765
IDLE = 600
last = time.time()


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global last
        last = time.time()
        # только этот компьютер: чужой адрес в запросе (DNS rebinding) и .git/.claude/.env — отказ
        if (self.headers.get('Host') or '').rsplit(':', 1)[0] not in ('localhost', '127.0.0.1'):
            self.send_error(400); return
        if self.path == '/__office-quit' and self.headers.get('X-Office') == '1':   # свой заголовок: чужая страница так не спросит
            self.send_response(204); self.end_headers(); threading.Timer(0.2, os._exit, (0,)).start(); return
        if '/.' in urllib.parse.unquote(self.path):
            self.send_error(404); return
        if self.path in ('/', '/index.html'):   # корень — сразу экран
            self.send_response(302); self.send_header('Location', urllib.parse.quote('/экран/офис.html')); self.end_headers(); return
        super().do_GET()

    def list_directory(self, path):   # списки папок не показываем
        self.send_error(404)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')   # события перечитываются раз в 2 с
        super().end_headers()

    def log_message(self, *a):
        pass


def watchdog():
    while time.time() - last < IDLE:
        time.sleep(30)
    os._exit(0)


Handler.extensions_map.update({'.js': 'text/javascript; charset=utf-8', '.md': 'text/plain; charset=utf-8',
                               '.html': 'text/html; charset=utf-8'})


def free():
    """Гасит экран офиса на порту (любой папки: этой он тоже не нужен — запустим заново)."""
    try:   # localhost, не 127.0.0.1: экран на PowerShell слушает только Host localhost
        urllib.request.urlopen(urllib.request.Request(f'http://localhost:{PORT}/__office-quit', headers={'X-Office': '1'}), timeout=2)
    except Exception:
        return
    time.sleep(1)


BUSY = (f'Порт {PORT} занят: экран офиса до v0.3.4 или другая программа. Закройте вкладку со старым экраном —'
        ' он погаснет сам через 10 минут, — или скажите Управляющему той папки «закончили».')


def start():
    http.server.ThreadingHTTPServer.allow_reuse_address = os.name != 'nt'   # Windows с ним пускает второй сервер на занятый порт
    try:
        return http.server.ThreadingHTTPServer(('127.0.0.1', PORT), functools.partial(Handler, directory=str(ROOT)))
    except OSError:
        return None


server = start() or (free(), start())[1]
if FREE:   # только освободить порт
    if server:
        server.server_close()
    sys.exit(0 if server else BUSY)
if not server:
    sys.exit(BUSY)
threading.Thread(target=watchdog, daemon=True).start()
server.serve_forever()
