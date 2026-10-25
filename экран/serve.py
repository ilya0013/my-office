"""Экран «Мой офис» для встроенного браузера Claude Code: он показывает файл без соседних
events.js и решения.js, поэтому экран отдаётся с localhost. Только чтение, только эта машина.
Сам выключается, если 10 минут нет запросов (открытый экран спрашивает раз в 2 с).
Запуск: python3 экран/serve.py [порт] — откройте http://localhost:<порт>/
"""
import functools, http.server, os, pathlib, sys, threading, time, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[1]   # папка проекта: экран ссылается на ../лиды и ../письма
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
IDLE = 600
last = time.time()


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global last
        last = time.time()
        # только этот компьютер: чужой адрес в запросе (DNS rebinding) и .git/.claude/.env — отказ
        if (self.headers.get('Host') or '').rsplit(':', 1)[0] not in ('localhost', '127.0.0.1'):
            self.send_error(400); return
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
threading.Thread(target=watchdog, daemon=True).start()
http.server.ThreadingHTTPServer(('127.0.0.1', PORT), functools.partial(Handler, directory=str(ROOT))).serve_forever()
