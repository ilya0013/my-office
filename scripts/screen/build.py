import re, sys, pathlib
SRC = pathlib.Path(__file__).parent / "cubicle-0.38.1.html"  # оригинал Cubicle 0.38.1, MIT
OUT = pathlib.Path(__file__).resolve().parents[2] / "экран" / "офис.html"
HERE = pathlib.Path(__file__).parent
h = SRC.read_text(encoding="utf-8")
adapter = (HERE / "mo-adapter.html").read_text(encoding="utf-8")
ru = (HERE / "mo-ru.js").read_text(encoding="utf-8")

def rep(old, new, count=1):
    global h
    n = h.count(old)
    if n != count:
        sys.exit(f"ожидал {count}, нашёл {n}: {old[:80]!r}")
    h = h.replace(old, new)

# 1. шапка документа
rep('<html lang="en">', '<html lang="ru">')
start = h.index('<title>'); end = h.index('</script>', start) + len('</script>\n')
h = h[:start] + '''<!--
  «Мой офис» — экран воркшопа. Основано на Cubicle 0.38.1 (https://github.com/caglarutkuguler/cubicle),
  MIT License, (c) 2026 Çağlar Utku Güler; текст лицензии — в LICENSE-cubicle.txt рядом с этим файлом.
  Изменения: данные из events.js вместо сервера, русский язык, панели конвейера, без сетевых функций.
-->
<title>Мой офис</title>
<meta name="description" content="Мой офис: живой пиксельный офис, где видно, кто из команды агентов чем занят.">
''' + h[end:]
# 2. адаптер событий и панели — до основного скрипта
rep('</style>\n</head>', '</style>\n' + adapter + '</head>')
# 3. видимые надписи
rep('<h1>Cubicle <small id="co"></small></h1>', '<h1>Мой офис <small id="co"></small></h1>')
rep('<span><a href="https://github.com/caglarutkuguler/cubicle" target="_blank" rel="noopener">Cubicle</a> · MIT</span>', '<span>Мой офис</span>')
# раскладка: две вкладки в одном окне — «Офис» (пиксельный офис) и «База» (все компании таблицей)
rep('''  <div id="main">
  <div id="stage">''', '''  <nav id="mo-view"><button type="button" data-view="office">Офис</button><button type="button" data-view="base">База<span id="mo-base-n"></span></button><span id="mo-status"></span></nav>
  <div id="mo-layout">
  <div id="mo-left">
  <div id="main">
  <div id="stage">''')
rep('''  <div id="cards"></div>
  </div>
''', '''  </div>
  </div>
  <section id="mo" class="mo-p">
    <div class="mo-base-head"><span id="mo-base-sum"></span><button type="button" class="mo-btn" id="mo-csv">Скачать для Excel</button></div>
    <div id="mo-base-table"></div>
    <div id="cards"></div>
  </section>
  </div>
''')
# компактная комната: 2 ряда по 3 стола, без крыльев; левая колонка столов и край лаунжа срезаны
s0 = h.index('  function layoutFor(n, force = false) {'); s1 = h.index("  window.addEventListener('resize', () => { if (AGENTS) layoutFor(AGENTS); });")
h = h[:s0] + '''  function layoutFor(n, force = false) {
    AGENTS = n;
    // Мой офис: ряды по 3 стола (минимум 2); OX < 0 сдвигает исходную комнату влево — так срезаются
    // её левая колонка столов, а CW на тайл меньше — правый край лаунжа с кофемашиной.
    const rows = Math.max(2, Math.ceil(n / 3));
    if (!force && rows === ROWS && WINGS === 1 && OX === -3.5 * T) return;
    ROWS = rows; WINGS = 1; OX = -3.5 * T;
    const rowsY = [3, 7.5]; for (let r = 3; r <= rows; r++) rowsY.push(10.5 + 3.5 * (r - 3));
    const at = (x, y) => { const d = [x + OX / T, y]; d.base = [x, y]; return d; };
    DESKS = [];
    for (const y of rowsY) for (const x of [4.5, 8, 11.5]) DESKS.push(at(x, y));
    CH = (rows === 2 ? 10.5 : 13 + (rows - 3) * 3.5) * T;
    CW = BASE_CW + OX - T;
    LOUNGE = BASE_LOUNGE.filter(([x, y]) => x < 20.6 && y < CH / T - 0.9).map(([x, y]) => [x + OX / T, y]);
    for (let r = 1; r <= rows - 3; r++) { const y = 10.5 + 3.5 * r; LOUNGE.push([16 + OX / T, y + 1], [17.8 + OX / T, y + 2], [19.6 + OX / T, y + 1]); }
    walk = null; queueKey = '';
    resizeCanvas();
    const shift = humanOn() ? 1 : 0;
    [...sprites.values()].sort((x, y) => x.idx - y.idx).forEach((sp, i) => { sp.desk = DESKS[(i + shift) % DESKS.length]; });
  }
''' + h[s1:]
rep("    rect('#4b4f6b', 0, 0, CW, 2 * T);\n    rect('#3a3d55', 0, 2 * T - 3, CW, 3);",
    "    rect('#4b4f6b', 0, 0, BASE_CW, 2 * T);\n    rect('#3a3d55', 0, 2 * T - 3, BASE_CW, 3);")   # стена на всю исходную комнату (она сдвинута на OX)
rep("const bubMax = Math.max(80, Math.floor(3.3 * T * k - 6)) + 'px';", "const bubMax = Math.max(150, Math.floor(4.6 * T * k)) + 'px';   // «ждёт сотрудников» целиком")
rep("const deskCount = Math.max(4, Math.min(DESKS.length, Math.ceil((sprites.size + (hum ? 1 : 0)) / 4) * 4));",
    "const deskCount = Math.max(6, Math.min(DESKS.length, Math.ceil((sprites.size + (hum ? 1 : 0)) / 3) * 3));")
rep("  resizeCanvas();\n  loadCatalog().then(applySettings).then(applyView);", "  layoutFor(0, true);\n  loadCatalog().then(applySettings).then(applyView);")
# офис сам подгоняет размер: во всю ширину окна, но не выше окна (под ним ничего нет — «База» отдельной вкладкой)
s0 = h.index('  function fitLayout() {'); s1 = h.index("  window.addEventListener('resize', () => fitLayout());")
h = h[:s0] + '''  function fitLayout() {
    if (!mainEl) return;
    const b = document.body;
    b.classList.remove('side');
    if (window.MO) window.MO.place();
    if (KIOSK || !animOn()) { b.classList.remove('fit'); return; }
    b.classList.add('fit');
    // холст с целым внутренним масштабом растянут CSS (pixelated)
    const wrap = document.querySelector('.wrap'), pad = 32;
    const maxH = Math.max(180, window.innerHeight - 130);   // 130 — шапка и вкладки
    const officeW = Math.min(window.innerWidth - pad, (maxH - 4) * CW / CH + 4);
    if (wrap) wrap.style.maxWidth = 'none';
    mainEl.style.setProperty('--stage-w', '100%');
    mainEl.style.setProperty('--stage-h', Math.floor((officeW - 4) * CH / CW + 4) + 'px');
    try { clampCam(); } catch (_) {}
  }
''' + h[s1:]
# команда — компактные строки; пути в шагах — ссылки
rep('    return `<div class="top"><span class="sw"', '    if (!panel && window.MO) return window.MO.teamRow(s, esc(L[s.status] || s.status)) + stepsHtml(s);\n    return `<div class="top"><span class="sw"')
rep("map(([t, text, d]) => `<li>${esc(text)} <span>", "map(([t, text, d]) => `<li>${window.MO ? window.MO.linkText(text) : esc(text)} <span>")
rep("      (animOn() ? own('layout', L.layout, [['auto', L.layoutAuto], ['side', L.layoutSide], ['stack', L.layoutStack]], settings.layout || 'auto') : '') +\n", "")
# 4. русский язык по умолчанию
rep('''  };
  const params = new URLSearchParams(location.search);''', '''  };
''' + ru + '''  const params = new URLSearchParams(location.search);''')
rep("(params.get('lang') || savedLang || navigator.language || 'en')", "(params.get('lang') || savedLang || 'ru')")
rep("const LANG_NAMES = { en: 'English',", "const LANG_NAMES = { ru: 'Русский', en: 'English',")
rep("const SPEECH_LANG = { en: 'en-US',", "const SPEECH_LANG = { ru: 'ru-RU', en: 'en-US',")
rep("id: 'pixel', name: { en: 'Pixel (classic)',", "id: 'pixel', name: { ru: 'Пиксели (классика)', en: 'Pixel (classic)',")
# 5. лента: текущий шаг для пузыря, моменты выдачи и сдачи работы
rep("{ identifier: String(t.id ?? t.identifier ?? ''), title: t.title ?? '', url: t.url || '' };",
    "{ identifier: String(t.id ?? t.identifier ?? ''), title: t.title ?? '', url: t.url || '', step: t.step || '' };")
rep("parent: a.parent ? `${path}#${a.parent}` : null, recent: Array.isArray(a.recent) ? a.recent : null,",
    "parent: a.parent ? `${path}#${a.parent}` : null, recent: Array.isArray(a.recent) ? a.recent : null,\n            assignedAt: a.assignedAt || null, returnedAt: a.returnedAt || null,")
rep("    setInterval(poll, 4000);\n", "    setInterval(poll, 2000);\n")
rep("document.title = labels.length ? `Cubicle · ${labels.join(' · ')}` : 'Cubicle';", "document.title = 'Мой офис';")
rep("if (!agents.length && providers.some((p) => p.kind === 'feed')) {",
    "if ((!agents.length || (window.MO && window.MO.empty())) && providers.some((p) => p.kind === 'feed')) {")
rep('''      s.recent = a.recent || null;
''', '''      s.recent = a.recent || null;
      // Мой офис: тот же сотрудник получил новое задание — конверт к нему; сдал работу — конверт Боссу
      const par = a.parent && sprites.get(a.parent);
      if (synced && par && a.assignedAt && s.assignedAt !== undefined && s.assignedAt !== a.assignedAt) sendEnvelope(par, s, '#dff1ff');
      if (synced && par && a.returnedAt && s.returnedAt !== undefined && s.returnedAt !== a.returnedAt) sendEnvelope(s, par, '#fff3c4');
      s.assignedAt = a.assignedAt || null; s.returnedAt = a.returnedAt || null;
''')
rep('''    if (s.typing && s.task) {
      // the task code''', '''    if (s.typing && s.task && s.task.step) return [s.task.step, 'task', s.task.title || ''];
    if (s.typing && s.task) {
      // the task code''')
rep("g.fillText(`Cubicle · ${officeName}`, 4, 4.8);", "g.fillText('Мой офис', 4, 4.8);")
rep("['✋ ' + ((t && t.identifier) || L.waitBubble), 'wait']", "[(t && t.identifier) ? '✋ ' + t.identifier : L.waitBubble, 'wait']")   # одна рука, не «✋ ✋ ждёт вас»
rep("a.download = 'cubicle-appearance.json';", "a.download = 'moy-ofis-vneshnost.json';")
rep("document.getElementById('co').textContent = labels.join(' · ');", "document.getElementById('co').textContent = window.MO ? window.MO.label : '';")
# 6. настройки: без серверных разделов (Telegram, настройки сервера)
rep("btn('set-cfg', '🛠 ' + C.title) + btn('set-tg', L.tgButton) + btn('set-copy',", "btn('set-copy',")
rep("panel.querySelector('#set-tg').addEventListener(", "panel.querySelector('#set-tg')?.addEventListener(")
rep("panel.querySelector('#set-cfg').addEventListener(", "panel.querySelector('#set-cfg')?.addEventListener(")

OUT.write_text(h, encoding="utf-8", newline="\n")
left = [l for l in re.findall(r"[^\n]*Cubicle[^\n]*", h) if "Cubicle" in l]
print("готово:", OUT, len(h), "байт; строк со словом Cubicle (код/скрытое):", len(left))
