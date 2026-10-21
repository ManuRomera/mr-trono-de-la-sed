"""Manual del Narrador y cuaderno de protagonistas: Markdown propio -> HTML -> Chrome -> PDF.

Texto siempre justificado y guionado (pyphen es). Las siluetas con borde irregular
(`@@fig ... left|right`) hacen que el texto las rodee mediante shape-outside.
Uso:  python3 tools/manual.py [--manual] [--players] [--sync]
  --sync   regenera content/narrative.json, readings.json y direction.json desde content/manual/*.md
"""
from pathlib import Path
import json, re, html, subprocess, sys, shutil
import pyphen
from PIL import Image

root = Path(__file__).resolve().parents[1]
SRC = root / 'content/manual'
OUT = root / 'output/pdf'; OUT.mkdir(parents=True, exist_ok=True)
WORK = root / 'editorial/web'; WORK.mkdir(parents=True, exist_ok=True)
CHROME = next((c for c in ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', shutil.which('google-chrome'), shutil.which('chromium')] if c and Path(c).exists()), 'google-chrome')
FONTS = root / 'editorial/fonts'
hy_es = pyphen.Pyphen(lang='es', left=3, right=3)

# ───────────────────────── Markdown propio ─────────────────────────
def inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<i>\1</i>', t)
    return t

def para_html(lines):
    return '<p>' + inline(' '.join(l.strip() for l in lines)) + '</p>'

def parse_blocks(lines, pdf):
    """Devuelve HTML para una lista de líneas (sin encabezados de sección)."""
    out = []; i = 0; n = len(lines)
    while i < n:
        l = lines[i]
        if not l.strip(): i += 1; continue
        if l.startswith('### '):
            j = i + 1
            while j < n and not lines[j].strip(): j += 1
            if pdf and j < n and lines[j].startswith('|'):
                k = j; rows = []
                while k < n and lines[k].startswith('|'):
                    rows.append([c.strip() for c in lines[k].strip().strip('|').split('|')]); k += 1
                rows = [r for r in rows if not all(re.fullmatch(r':?-{2,}:?', c) for c in r)]
                if len(rows[0]) >= 3:
                    out.append('<div class="mr-wide keep"><h3>' + inline(l[4:].strip()) + '</h3>' + table_html(rows) + '</div>'); i = k; continue
            out.append('<h3>' + inline(l[4:].strip()) + '</h3>'); i += 1; continue
        if l.startswith('@@'):
            if pdf: out.append(directive(l))
            i += 1; continue
        if l.startswith('>'):
            paras = []; cur = []
            while i < n and lines[i].startswith('>'):
                s = lines[i][1:].strip()
                if not s:
                    if cur: paras.append(cur); cur = []
                else: cur.append(s)
                i += 1
            if cur: paras.append(cur)
            out.append('<blockquote>' + ''.join(para_html(p) for p in paras) + '</blockquote>'); continue
        if l.startswith(':::'):
            head = l[3:].strip(); kind, _, title = head.partition(' ')
            body = []; i += 1
            while i < n and not lines[i].startswith(':::'): body.append(lines[i]); i += 1
            i += 1
            out.append(box_html(kind, title.strip(), body, pdf)); continue
        if l.startswith('|'):
            rows = []
            while i < n and lines[i].startswith('|'):
                rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')]); i += 1
            rows = [r for r in rows if not all(re.fullmatch(r':?-{2,}:?', c) for c in r)]
            t = table_html(rows)
            out.append(f'<div class="mr-wide">{t}</div>' if pdf and len(rows[0]) >= 3 else t); continue
        if re.match(r'[-•] ', l):
            items = []
            while i < n and re.match(r'[-•] ', lines[i]):
                items.append('<li>' + inline(lines[i][2:].strip()) + '</li>'); i += 1
            out.append('<ul>' + ''.join(items) + '</ul>'); continue
        if re.match(r'\d+\. ', l):
            items = []
            while i < n and re.match(r'\d+\. ', lines[i]):
                items.append('<li>' + inline(re.sub(r'^\d+\.\s+', '', lines[i]).strip()) + '</li>'); i += 1
            out.append('<ol>' + ''.join(items) + '</ol>'); continue
        buf = []
        while i < n and lines[i].strip() and not re.match(r'(>|:::|\||@@|### |[-•] |\d+\. )', lines[i]):
            buf.append(lines[i]); i += 1
        out.append(para_html(buf))
    return ''.join(out)

def table_html(rows):
    head, *body = rows
    return ('<table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead><tbody>' +
            ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in body) + '</tbody></table>')

def box_html(kind, title, body, pdf):
    if kind == 'pnj':   # Nombre · oficio  /  Clave. texto
        fields = []; free = []
        for l in body:
            m = re.match(r'([A-ZÁÉÍÓÚa-záéíóúñ ]{3,18})\.\s+(.*)', l)
            if m: fields.append((m.group(1), m.group(2)))
            elif l.strip(): free.append(l)
        return ('<section class="mr-npc"><h4>' + inline(title) + '</h4>' +
                ''.join(f'<p><b>{inline(k)}.</b> {inline(v)}</p>' for k, v in fields) +
                (parse_blocks(free, pdf) if free else '') + '</section>')
    if kind == 'doc':
        return '<section class="mr-doc"><h4>' + inline(title) + '</h4>' + parse_blocks(body, pdf) + '</section>'
    if kind == 'ancho':
        return '<section class="mr-wide">' + parse_blocks(body, pdf) + '</section>'
    inner = parse_blocks(body, pdf)
    if pdf and inner.count('<table') == 1 and re.sub(r'<div class="mr-wide">.*?</table></div>', '', inner, flags=re.S) == '':
        return '<div class="mr-wide"><h4 class="wt">' + inline(title) + '</h4>' + inner.replace('<div class="mr-wide">', '', 1)[:-6] + '</div>'
    return '<section class="mr-box"><h4>' + inline(title) + '</h4>' + inner + '</section>'

def directive(l):
    """@@fig nombre left|right|full|col w=34mm cap="Pie"   |  @@pagebreak"""
    m = re.match(r'@@(\w+)\s*(.*)', l.strip()); kind, rest = m.group(1), m.group(2)
    if kind == 'fig':
        name = rest.split()[0]
        opts = {k: v.strip('"') for k, v in re.findall(r'(\w+)=("[^"]*"|\S+)', rest)}
        side = next((w for w in ('left', 'right', 'full', 'col') if re.search(r'\b' + w + r'\b', rest)), 'col')
        return figure(name, side, opts.get('w'), opts.get('cap', ''))
    if kind == 'pagebreak': return '<div class="pb"></div>'
    return ''

# ───────────────────────── Imágenes ─────────────────────────
def find_art(name):
    for c in [root / f'assets/npc/{name}-token.webp', root / f'assets/characters/{name}-token.webp',
              root / f'art/masters/{name}.png', root / f'editorial/plates/{name}.webp',
              root / f'editorial/plates/{name.removeprefix("scene-")}.webp', root / f'assets/objects/{name}.webp',
              root / f'assets/maps/{name.removeprefix("mapa-")}.webp', root / f'assets/maps/{name}.webp',
              root / f'assets/scenes/{name.removeprefix("scene-")}.webp', root / f'assets/npc/{name}.webp']:
        if c.exists(): return c
    raise FileNotFoundError(name)

def web_image(name, maxw=1500, alpha=False):
    src = find_art(name); ext = 'png' if alpha else 'jpg'
    dst = WORK / f'{name}-{maxw}.{ext}'
    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
        im = Image.open(src).convert('RGBA')
        if alpha:
            bb = im.getchannel('A').point(lambda p: 255 if p > 24 else 0).getbbox()
            if bb: im = im.crop(bb)
            im.thumbnail((maxw, maxw * 2)); im.save(dst, optimize=True)
        else:
            bg = Image.new('RGBA', im.size, '#f6f0e3'); bg.alpha_composite(im); im = bg.convert('RGB')
            im.thumbnail((maxw, maxw * 2)); im.save(dst, quality=88)
    return dst.name

def is_cutout(name):
    try:
        im = Image.open(find_art(name))
        return im.mode == 'RGBA' and im.getchannel('A').getextrema()[0] < 20
    except Exception: return False

def figure(name, side, w, cap, cut=False):
    if is_cutout(name):
        f = web_image(name, 600, alpha=True); w = w or '36mm'
        return (f'<figure class="cut {side}" style="width:{w};shape-outside:url({f}) content-box"><img src="{f}" alt="">'
                + (f'<figcaption>{inline(cap)}</figcaption>' if cap else '') + '</figure>')
    f = web_image(name, 1500)
    return (f'<figure class="pic {side}"' + (f' style="width:{w}"' if w else '') + f'><img src="{f}" alt="">' +
            (f'<figcaption>{inline(cap)}</figcaption>' if cap else '') + '</figure>')

# ───────────────────────── Carga de capítulos ─────────────────────────
def load_chapters(pdf):
    chapters = []
    for p in sorted(SRC.glob('*.md')):
        txt = p.read_text(encoding='utf-8')
        m = re.match(r'---\n(.*?)\n---\n(.*)', txt, re.S)
        meta = {}
        for l in m.group(1).split('\n'):
            if ':' in l: k, v = l.split(':', 1); meta[k.strip()] = v.strip()
        sections = []; cur = None; lead = []
        for l in m.group(2).split('\n'):
            if l.startswith('## '):
                if cur: sections.append(cur)
                title = l[3:].strip(); attrs = {}
                am = re.search(r'\{(.*?)\}\s*$', title)
                if am:
                    attrs = {k: v.strip() for k, v in re.findall(r'(\w+)=([^;]+)', am.group(1))}; title = title[:am.start()].strip()
                cur = {'title': title, 'attrs': attrs, 'lines': []}
            elif cur is None: lead.append(l)
            else: cur['lines'].append(l)
        if cur: sections.append(cur)
        for s in sections:
            s['body'] = parse_blocks(s['lines'], False)
            s['pdf'] = parse_blocks(s['lines'], True)
        meta['sections'] = sections; meta['intro'] = parse_blocks(lead, pdf) if ''.join(lead).strip() else ''
        chapters.append(meta)
    return chapters

# ───────────────────────── Sincronización con Foundry ─────────────────────────
def sync():
    """narrative.json (capítulos), readings.json y direction.json se derivan del Markdown."""
    chapters = load_chapters(False)
    story = json.loads((root / 'content/narrative.json').read_text())
    story['chapters'] = [{'id': c['id'], 'title': c['title'], 'audience': c.get('audience', 'gm'),
                          'sections': [{'title': s['title'], 'body': s['body']} for s in c['sections']]} for c in chapters]
    pres = json.loads((root / 'content/presentations.json').read_text())
    story['chapters'].append({'id': 'presentaciones', 'title': 'Rostros ante la lámpara', 'audience': 'gm', 'sections': [
        {'title': n, 'body': '<blockquote>' + ''.join(f'<p>{p}</p>' for p in ps) + '</blockquote>'} for n, ps in pres.items()]})
    (root / 'content/narrative.json').write_text(json.dumps(story, ensure_ascii=False, indent=1))
    direction = json.loads((root / 'content/direction.json').read_text())
    where = {}
    for c in chapters:
        for i, s in enumerate(c['sections']):
            if 'slug' in s['attrs']:
                for slug in s['attrs']['slug'].split(','): where[slug.strip()] = (c['id'], i, s)
    readings = {}
    for d in direction:
        if 'aliasOf' in d: continue
        if d['slug'] not in where: raise SystemExit('Escena sin sección en el Markdown: ' + d['slug'])
        cid, i, s = where[d['slug']]; d['chapter'] = cid; d['section'] = i
        qs = re.findall(r'<blockquote>(.*?)</blockquote>', s['body'], re.S)
        if not qs: raise SystemExit('Sin lectura: ' + d['slug'])
        readings[d['slug']] = [p for q in qs for p in re.findall(r'<p>(.*?)</p>', q, re.S)]
    for d in direction:
        if 'aliasOf' in d:
            t = next(x for x in direction if x['slug'] == d['aliasOf']); d['chapter'] = t['chapter']; d['section'] = t['section']
    (root / 'content/direction.json').write_text(json.dumps(direction, ensure_ascii=False, indent=1))
    (root / 'content/readings.json').write_text(json.dumps(readings, ensure_ascii=False, indent=1))
    print('sync ok:', len(chapters), 'capítulos,', sum(len(c['sections']) for c in chapters), 'secciones,', len(readings), 'lecturas')

# ───────────────────────── Guionado ─────────────────────────
WORD = re.compile(r'(?<![\w’-])[a-záéíóúñü]{7,}(?![\w’-])')
def hy(t):
    return WORD.sub(lambda m: hy_es.inserted(m.group(0), hyphen='­'), t)

def hyphenate(doc):
    def fix(m):
        inner = re.sub(r'(>)([^<]+)(<)', lambda k: k.group(1) + hy(k.group(2)) + k.group(3), '>' + m.group(2) + '<')[1:-1]
        return m.group(1) + inner + m.group(3)
    return re.sub(r'(<(?:p|li|td|figcaption)\b[^>]*>)(.*?)(</(?:p|li|td|figcaption)>)', fix, doc, flags=re.S)

# ───────────────────────── CSS ─────────────────────────
CSS = '''
@font-face{font-family:"EBG";src:url("fonts/EBGaramond-Regular.ttf");font-weight:400}
@font-face{font-family:"EBG";src:url("fonts/EBGaramond-Italic.ttf");font-weight:400;font-style:italic}
@font-face{font-family:"EBG";src:url("fonts/EBGaramond-Bold.ttf");font-weight:700}
@font-face{font-family:"Cin";src:url("fonts/cinzel/CinzelDecorative-Regular.ttf");font-weight:400}
@font-face{font-family:"Cin";src:url("fonts/cinzel/CinzelDecorative-Bold.ttf");font-weight:700}
@font-face{font-family:"Cin";src:url("fonts/cinzel/CinzelDecorative-Black.ttf");font-weight:900}
:root{--ink:#25242b;--ruby:#713447;--gold:#a78850;--paper:#f6f0e3;--paper2:#ece2d0;--night:#1b2434}
@page{size:210mm 297mm;margin:22mm 16mm 22mm 16mm;background:#f6f0e3;
 @bottom-center{content:counter(page);font:8.5pt "EBG";color:#6b5c4b}
 @top-left{content:string(run);font:700 7.6pt "EBG";letter-spacing:.14em;color:#713447}
 @top-right{content:"MANUAL DEL NARRADOR";font:7.6pt "EBG";letter-spacing:.14em;color:#6b5c4b}}
@page cover{margin:0;@bottom-center{content:none}@top-left{content:none}@top-right{content:none}}
@page plate{margin:0;@bottom-center{content:none}@top-left{content:none}@top-right{content:none}}
@page front{@top-left{content:none}@top-right{content:none}@bottom-center{content:none}}
*{box-sizing:border-box}
html{background:var(--paper);-webkit-print-color-adjust:exact;print-color-adjust:exact}
body{margin:0;font:10.6pt/1.4 "EBG","Garamond",Georgia,serif;color:var(--ink);text-align:justify;hyphens:manual;
 font-variant-numeric:lining-nums;orphans:3;widows:3;text-rendering:geometricPrecision}
p{margin:0 0 2.3mm}
h1,h2,h3,h4{break-after:avoid;text-align:left;margin:0}
.cover{page:cover;width:210mm;height:297mm;position:relative;overflow:hidden;background:#0c0e14;color:#f5ecd7;break-after:page}
.cover img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.cover .veil{position:absolute;left:0;right:0;bottom:0;height:46%;background:linear-gradient(to top,rgba(5,6,10,.96),rgba(5,6,10,0))}
.cover .t{position:absolute;left:0;right:0;text-align:center;font-family:Cin;letter-spacing:.1em}
.cover .k{top:11mm;font:700 9pt "EBG";letter-spacing:.3em;color:#c8a46d}
.cover .el{bottom:96mm;font-size:17pt;color:#c8a46d;letter-spacing:.3em}
.cover .trono{bottom:68mm;font-size:62pt;font-weight:900;line-height:1;text-shadow:0 .8mm 0 #742731}
.cover .dela{bottom:62mm;font-size:15pt;color:#c8a46d;letter-spacing:.35em}
.cover .sed{bottom:30mm;font-size:76pt;font-weight:900;line-height:1;text-shadow:0 .8mm 0 #742731}
.cover .sub{bottom:22mm;font-size:11pt;font-weight:700;color:#c8a46d;letter-spacing:.08em}
.cover .au{bottom:13mm;font-size:11.5pt;font-weight:700;letter-spacing:.18em}
.cover .ed{bottom:7mm;font:9pt "EBG";letter-spacing:.1em;color:#c8a46d}
.plate{page:plate;width:210mm;height:297mm;position:relative;overflow:hidden;break-before:page;break-after:page;color:var(--paper)}
.plate img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.plate .veil{position:absolute;left:0;right:0;bottom:0;height:68mm;background:linear-gradient(to top,rgba(14,19,31,.94) 55%,rgba(14,19,31,0))}
.plate .txt{position:absolute;left:16mm;right:16mm;bottom:16mm;text-align:left}
.plate .kick{font:700 9pt "EBG";letter-spacing:.2em;color:#d4b776;margin-bottom:2mm}
.plate h1{font:900 30pt/1.05 Cin;color:var(--paper);margin-bottom:4mm}
.plate .q{font-style:italic;font-size:13pt;line-height:1.35;color:var(--paper);max-width:150mm}
.front{page:front;break-before:page;break-after:page}
.front h1{font:900 22pt/1.1 Cin;color:var(--ruby);margin-bottom:4mm;text-align:left}
.front .lead{font-style:italic;font-size:12pt;margin-bottom:6mm}
.toc{margin-top:5mm;font-size:11pt}
.toc div{display:flex;align-items:baseline;gap:2mm;margin:0 0 1.2mm;text-align:left}
.toc .d{flex:1;border-bottom:1px dotted #9d8c70;transform:translateY(-1.5mm)}
.toc .l1{font-weight:700;margin-top:2.6mm;color:var(--ruby)}
.toc .l2{padding-left:5mm;font-size:10.3pt}
.chapter{break-before:page}
.chapter .head{column-span:all;margin:0 0 6mm;border-bottom:.5mm solid var(--gold);padding-bottom:2.5mm;string-set:run attr(data-run)}
.chapter .head .num{font:700 9pt "EBG";letter-spacing:.22em;color:var(--gold);text-align:left}
.chapter .head h1{font:700 23pt/1.08 Cin;color:var(--ruby);letter-spacing:.01em;margin-top:1.5mm}
.chapter .head .sub{font-style:italic;font-size:12pt;margin-top:2mm;text-align:left;color:#4d4136}
.cols{column-count:2;column-gap:8mm;column-fill:balance}
.cols>p:first-of-type::first-letter{font:900 41pt/.82 Cin;color:var(--ruby);float:left;margin:1.4mm 1.6mm -1mm 0}
h2{font-variant:small-caps;font-weight:700;font-size:14.5pt;letter-spacing:.045em;line-height:1.12;color:var(--ruby);
 margin:5mm 0 2.4mm;padding-bottom:1.2mm;border-bottom:.3mm solid var(--gold);position:relative}
h2 .key{font:700 11.5pt/1 "EBG";letter-spacing:.06em;background:var(--ruby);color:var(--paper);padding:.9mm 2.2mm .7mm;margin-right:2.6mm;border-radius:.7mm;font-variant:normal;display:inline-block;transform:translateY(-.4mm)}
h2 .time{font:italic 400 9pt "EBG";font-variant:normal;letter-spacing:.02em;color:#6b5c4b;float:right;margin-top:1.2mm}
h2.first{margin-top:0}
h3{font:700 11pt "EBG";font-variant:small-caps;letter-spacing:.06em;color:#4c2a36;margin:3.4mm 0 1.2mm}
h4{font:700 10.4pt "EBG";font-variant:small-caps;letter-spacing:.07em;color:var(--ruby);margin:0 0 1.6mm}
blockquote{margin:2.4mm 0 3.4mm;padding:2.6mm 3.4mm 1mm 4.2mm;background:rgba(113,52,71,.075);border-left:1.3mm solid var(--ruby);
 font-size:10.2pt;line-height:1.38;break-inside:auto;color:#2b2830}
blockquote p{margin:0 0 2.1mm}
.mr-box{background:var(--paper2);border:.35mm solid var(--gold);padding:3mm 3.6mm 1.2mm;margin:3.4mm 0 4mm;break-inside:avoid;font-size:10pt;line-height:1.36}
.mr-box p{margin:0 0 2mm}
.mr-box ul{margin:0 0 2mm 4mm;padding:0}
.mr-npc{background:var(--paper2);border-top:.9mm solid var(--ruby);border-bottom:.3mm solid var(--gold);padding:2.2mm 3.2mm .8mm;margin:2.6mm 0 3.2mm;font-size:9.6pt;line-height:1.3;break-inside:avoid}
.mr-npc h4{font-size:11.2pt}
.mr-npc p{margin:0 0 1.5mm}
.mr-doc{background:#efe3c8;border:.3mm solid #b49a68;box-shadow:inset 0 0 8mm rgba(120,84,30,.22);padding:4mm 5mm 2mm;margin:3.5mm 1mm 4.5mm;font-style:italic;font-size:10.8pt;line-height:1.46;break-inside:avoid}
.mr-doc h4{font-style:normal;text-align:center;font-size:10.8pt;letter-spacing:.14em}
.mr-doc p{text-align:left;margin-bottom:2.2mm}
.mr-wide{column-span:all;margin:3mm 0}
.mr-wide.keep{break-inside:avoid}
.mr-wide h4.wt{font-size:11pt;margin:0 0 1mm}
ul,ol{margin:0 0 2.3mm 4.2mm;padding:0}ol{margin-left:5mm}li{margin:0 0 1mm}
table{width:100%;border-collapse:collapse;font-size:9.4pt;line-height:1.28;margin:2.4mm 0 4mm;break-inside:avoid;text-align:left}
th{background:#d8c7a5;font-variant:small-caps;letter-spacing:.05em;padding:1.4mm 2mm;border:.25mm solid var(--gold);text-align:left}
td{padding:1.3mm 2mm;border:.25mm solid #cbb88f;vertical-align:top;hyphens:manual}
tr:nth-child(even) td{background:rgba(236,226,208,.55)}
figure{margin:0}figcaption{font-style:italic;font-size:8.8pt;line-height:1.25;color:#645646;text-align:left;margin-top:1mm}
figure.pic{margin:2.4mm 0 3.4mm;break-inside:avoid}
figure.pic img{width:100%;display:block;border:.3mm solid var(--gold)}
figure.pic.full{column-span:all;margin:3mm 0 4mm}
figure.cut{break-inside:avoid;shape-image-threshold:.35;shape-margin:3.2mm}
figure.cut img{width:100%;display:block}
figure.cut.left{float:left;margin:0 4mm 1mm 0}
figure.cut.right{float:right;margin:0 0 1mm 4mm}
.pb{break-after:page}
.tight blockquote{font-size:9.8pt;line-height:1.32;padding-top:2mm}.tight h2{margin-top:3.4mm}.tight .cols>p{display:none}
.sheet{break-before:page;position:relative}
.sheet.first{break-before:avoid}
.sheet .nm{font:900 26pt/1 Cin;color:var(--ruby);text-align:left}
.sheet .sd{font-style:italic;font-size:12.4pt;margin:1mm 0 4mm;color:#4d4136;text-align:left}
.sheet .top{overflow:hidden;margin-bottom:4mm;min-height:92mm}
.sheet .top figure{float:left;width:44mm;margin:0 5mm 1mm 0;shape-margin:3mm}
.sheet .top figure img{width:100%;display:block}
.sheet .top p{font-size:9.7pt;line-height:1.3;margin-bottom:1.6mm}
.themes{display:grid;grid-template-columns:1fr 1fr;border:.3mm solid var(--gold);background:var(--paper2);text-align:left}
.themes>div{padding:2.2mm 3mm 1.2mm;border:.15mm solid var(--gold);font-size:9.4pt;line-height:1.26}
.themes h4{font-size:11.5pt;margin-bottom:1.2mm}
.themes p{margin:0 0 1mm;text-align:left}
.sheet .foot{margin-top:3mm;font-size:9.8pt;line-height:1.32;text-align:left}
.stat{break-inside:avoid;border-top:.5mm solid var(--ruby);padding-top:1.4mm;margin-top:2.4mm}
.stat h3{font-size:12.4pt;margin:0 0 1mm}
.stat p{margin:0 0 1mm;font-size:9.6pt;line-height:1.3}
.handout{break-inside:avoid;background:#efe3c8;border:.3mm solid #b49a68;box-shadow:inset 0 0 8mm rgba(120,84,30,.22);padding:3.4mm 4.4mm 1.4mm;margin:0 0 4mm;font-size:10.8pt;font-style:italic;line-height:1.42}
.handout h4{text-align:center;font-style:normal;letter-spacing:.14em}
.handout p{text-align:left;margin-bottom:2mm}
'''

# ───────────────────────── Piezas del libro ─────────────────────────
def plate_html(art, title, kicker, quote):
    f = web_image(art, 2000)
    return (f'<div class="plate"><img src="{f}" alt=""><div class="veil"></div><div class="txt"><div class="kick">{inline(kicker.upper())}</div>'
            f'<h1>{title}</h1><div class="q">{inline(quote)}</div></div></div>')

def cover_html(kind):
    f = web_image('scene-neb-sekhem', 2000)
    return (f'<div class="cover"><img src="{f}" alt=""><div class="veil"></div>'
            '<div class="t k">UNA AVENTURA DE HORROR GÓTICO</div><div class="t el">EL</div><div class="t trono">TRONO</div>'
            '<div class="t dela">DE LA</div><div class="t sed">SED</div><div class="t sub">LA CORTE DEL REY SIN NOMBRE</div>'
            f'<div class="t au">MANUEL ROMERA</div><div class="t ed">{kind.upper()} · LEGEND IN THE MIST</div></div>')

def zone_title(title):
    """«M1. La puerta de Hori · 20 minutos» -> clave + título + tiempo."""
    m = re.match(r'^([A-Z]\d+[a-z]?)\.\s+(.*?)(?:\s+·\s+(.*))?$', title)
    if not m: return inline(title)
    key, t, tm = m.groups()
    return f'<span class="key">{key}</span>{inline(t)}' + (f'<span class="time">{inline(tm)}</span>' if tm else '')

def chapter_html(c):
    out = []
    plate = c.get('plate')
    if plate:
        art, title, kicker, quote = [x.strip() for x in plate.split('|')]
        out.append(plate_html(art, title, kicker, quote))
    run = c.get('run', c['title']).upper()
    out.append(f'<div class="chapter">')
    out.append(f'<div class="head" data-run="{html.escape(run)}"><div class="num">{inline(c.get("num", "").upper())}</div>'
               f'<h1 id="{c["id"]}">{inline(c["title"])}</h1>' + (f'<div class="sub">{inline(c["sub"])}</div>' if c.get('sub') else '') + '</div>')
    out.append('<div class="cols">')
    out.append(c.get('intro', ''))
    for i, s in enumerate(c['sections']):
        out.append(f'<h2 id="{c["id"]}-{i}" class="{"first" if (i == 0 and not c.get("intro")) else ""}">{zone_title(s["title"])}</h2>' + s['pdf'])
    out.append('</div></div>')
    return ''.join(out)

def toc_html(chapters, pages=None):
    rows = ['<div class="toc">']
    for c in chapters:
        label = (c.get('num', '').split(' · ')[0] + ' · ' if c.get('num') else '') + re.sub(r'<[^>]+>', '', inline(c['title']))
        pg = pages.get(c['id'], '') if pages else ''
        rows.append(f'<div class="l1"><span>{label}</span><span class="d"></span><span>{pg}</span></div>')
        for i, s in enumerate(c['sections']):
            if re.match(r'^[A-Z]\d+', s['title']) or c.get('toc') == 'all':
                t = re.sub(r'\s+·\s+.*$', '', s['title']) if re.match(r'^[A-Z]\d+', s['title']) else s['title']
                pg = pages.get(f'{c["id"]}-{i}', '') if pages else ''
                rows.append(f'<div class="l2"><span>{html.escape(t)}</span><span class="d"></span><span>{pg}</span></div>')
    rows.append('</div>')
    return ''.join(rows)

def load(name): return json.loads((root / name).read_text())

def hero_sheet(a, secrets, first=False):
    s = a['system']; slug = a['name'].lower()
    bio_html = s['biography'].split('</blockquote>', 1)[-1]
    bio_html = re.sub(r'<h3>(.*?)</h3>\s*<p>', r'<p><b>\1.</b> ', bio_html)
    f = web_image(slug, 700, alpha=True)
    themes = [i for i in a['items'] if i['type'] == 'themebook']
    cells = ''
    for it in themes:
        ss = it['system']
        cells += ('<div><h4>' + html.escape(it['name']) + '</h4><p><b>Motivación.</b> ' + html.escape(ss['quest']) + '</p>' +
                  ''.join('<p>• ' + html.escape(t['name']) + '</p>' for t in ss.get('powertags', []) if not t.get('planned')) +
                  '<p><b>Debilidad.</b> ' + html.escape(' · '.join(t['name'] for t in ss.get('weaknesstags', []))) + '</p></div>')
    eq = ' · '.join(t['name'] for i in a['items'] if i['type'] == 'backpack' for t in i['system'].get('items', []))
    rel = s.get('fellowships', [{}])[0]
    return (f'<section class="sheet{" first" if first else ""}"><div class="nm">{html.escape(a["name"])}</div><div class="sd">{html.escape(s["shortDescription"])}</div>'
            f'<div class="top"><figure style="shape-outside:url({f}) content-box"><img src="{f}" alt=""></figure>{bio_html}</div>'
            f'<div class="themes">{cells}</div>'
            f'<p class="foot"><b>Equipo.</b> {html.escape(eq)}<br><b>Relación con {html.escape(rel.get("companion", ""))}.</b> {html.escape(rel.get("relationshipTag", ""))}</p></section>')

def stat_blocks(actors):
    out = ''
    for a in actors:
        s = a['system']
        if a['type'] != 'litm-npc' or (not s.get('limits') and not s.get('threatsAndConsequences')): continue
        out += f'<div class="stat"><h3>{html.escape(a["name"])}</h3>'
        if s.get('shortDescription'): out += f'<p>{html.escape(s["shortDescription"])}</p>'
        for lim in s.get('limits', []): out += f'<p><b>{html.escape(lim["name"])} {html.escape(str(lim["value"]))}.</b> {html.escape(lim.get("consequence", ""))}</p>'
        for asp in s.get('mightyAspects', []): out += f'<p><b>Might.</b> {html.escape(asp.get("level", ""))} · {html.escape(asp.get("aspect", ""))}</p>'
        for f in s.get('specialFeatures', []): out += f'<p><b>{f["name"]}.</b> {f["description"]}</p>'
        for t in s.get('threatsAndConsequences', []):
            out += f'<p><b>{t["name"]}.</b> {t.get("description", "")}</p>'
            for x in t.get('list', []): out += f'<p>• {x}</p>'
        out += '</div>'
    return out

def doc_html(story, which='gm'):
    out = ''
    for h in story['handouts']:
        initial = h.get('reveal') == 'initial'
        if (which == 'gm' and not initial) or (which == 'players' and initial):
            out += f'<div class="handout"><h4>{html.escape(h["title"])}</h4>{h["body"]}</div>'
    return out

def render(doc_html_, name, header='MANUAL DEL NARRADOR'):
    (WORK / 'book.css').write_text(CSS.replace('"MANUAL DEL NARRADOR"', '"' + header + '"'))
    for f in FONTS.rglob('*.ttf'):
        dest = WORK / 'fonts' / f.relative_to(FONTS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if not dest.exists(): shutil.copy(f, dest)
    page = f'<!doctype html><html lang="es"><meta charset="utf-8"><title>El Trono de la Sed</title><link rel="stylesheet" href="book.css"><body>{doc_html_}</body></html>'
    (WORK / f'{name}.html').write_text(hyphenate(page))
    pdf = OUT / f'{name}.pdf'
    subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer', '--allow-file-access-from-files',
                    '--virtual-time-budget=20000', f'--print-to-pdf={pdf}', (WORK / f'{name}.html').as_uri()],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Chrome can paint the first glyph of the following heading outside the cover.
    # Print the cover alone and assemble the book; preserve every content page and link.
    cover = re.match(r'(<div class="cover">.*?</div></div>)', doc_html_, re.S)
    if cover:
        import hashlib
        from pypdf import PdfReader, PdfWriter
        key = hashlib.sha256(('standalone-cover-v2' + cover.group(1) + CSS).encode()).hexdigest()[:16]
        cover_pdf = WORK / f'cover-{key}.pdf'
        if not cover_pdf.exists():
            cover_html = WORK / f'cover-{key}.html'
            cover_html.write_text('<!doctype html><html lang="es"><meta charset="utf-8"><link rel="stylesheet" href="book.css"><body>' + hyphenate(cover.group(1)) + '</body></html>')
            subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
                            '--allow-file-access-from-files', '--virtual-time-budget=20000',
                            f'--print-to-pdf={cover_pdf}', cover_html.as_uri()],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clean = PdfReader(cover_pdf)
        if len(clean.pages) != 1:
            raise RuntimeError('La portada debe ocupar exactamente una página')
        original = PdfReader(pdf)
        writer = PdfWriter()
        writer.append(clean)
        writer.append(original, pages=(1, len(original.pages)))
        temporary = pdf.with_suffix('.clean.pdf')
        with temporary.open('wb') as stream: writer.write(stream)
        temporary.replace(pdf)
    return pdf

def locate(pdf, chapters, start=2):
    """Página de cada capítulo y zona buscando su título en el PDF (segunda pasada del índice)."""
    import fitz
    d = fitz.open(pdf); pages = {}
    texts = [re.sub(r'\s+', ' ', d[i].get_text().replace('­', '')).lower() for i in range(len(d))]
    def find(t, frm):
        t = re.sub(r'\s+', ' ', t).lower()
        for i in range(frm, len(texts)):
            if t in texts[i]: return i
        return None
    cur = start
    for c in chapters:
        p = find(re.sub(r'<[^>]+>', '', inline(c['title'])), cur)
        if p is not None: pages[c['id']] = p + 1; cur = p
        for i, s in enumerate(c['sections']):
            t2 = re.sub(r'\s+·\s+.*$', '', s['title']) if re.match(r'^[A-Z]\d+', s['title']) else s['title']; m = re.match(r'^([A-Z]\d+[a-z]?)\.\s+(.*)$', t2)
            p = find(m.group(2) if m else t2, cur)
            if p is not None: pages[f'{c["id"]}-{i}'] = p + 1; cur = p
    return pages

def closing_html():
    audio = load('content/audio.json')
    music = ''.join(f'<p style="margin:0 0 1mm;font-size:9.6pt">{html.escape(d["name"])} · «{html.escape(d["title"])}» — Kevin MacLeod.</p>' for d in audio if d['kind'] == 'music')
    notice = ''
    for para in (root / 'NOTICE.md').read_text().split('\n\n'):
        if para.startswith('#'): notice += '<h3>' + html.escape(para.lstrip('# ').strip()) + '</h3>'
        elif not para.startswith('Fuentes consultadas:'): notice += '<p style="font-size:9.6pt">' + html.escape(para).replace('\n', '<br>') + '</p>'
    return ('<div class="chapter"><div class="head" data-run="FOUNDRY, AUTORÍA Y EDICIÓN"><div class="num">COLOFÓN</div><h1 id="colophon">Foundry, autoría y edición</h1></div><div class="cols">'
            '<p>Instala mist-engine-fvtt 14.5.4 en Foundry v13. Descomprime el módulo en Data/modules y actívalo en un mundo del sistema; acepta la importación en un mundo vacío o usa Configuración → MR · El Trono de la Sed → Libro de los Muertos → Importar la aventura. La barra del Narrador, los diarios de escena, las listas de audio y las fichas nativas se enlazan desde esa importación.</p>'
            '<h3>Banda sonora instrumental</h3><p style="font-size:9.6pt">Música de Kevin MacLeod (incompetech.com), Creative Commons Attribution 4.0. Edición: recorte, bucle y normalización.</p>' + music + notice + '</div></div>')

def build_manual():
    chapters = [c for c in load_chapters(True) if c.get('audience', 'gm') != 'players']
    story = load('content/narrative.json'); actors = load('content/actors.json'); secrets = load('content/personal-secrets.json')
    heroes = [a for a in actors if a['type'] == 'litm-character']
    front = ('<div class="front"><h1>Índice</h1><div class="lead">Un funeral sin nombre, una corte bajo la arena y la decisión de quién merece ser recordado.</div>@@TOC@@'
             '<p style="margin-top:8mm;font-size:9.4pt;text-align:left">MANUEL ROMERA · PROYECTO MR · Edición 1.2.0 · Para Legend in the Mist en Foundry VTT.</p></div>')
    body = [chapter_html(c) for c in chapters]
    body.append(plate_html('lamina-corazon', 'Lo que aún puede salvarse', 'Los protagonistas', 'La piedra recuerda el peso de cada nombre. Vosotros decidís quién vuelve a pronunciarlo.'))
    body.append('<div class="chapter"><div class="head" data-run="LOS CINCO PROTAGONISTAS"><div class="num">APÉNDICE D</div><h1 id="heroes">Los cinco protagonistas</h1></div>' + hero_sheet(heroes[0], secrets, True) + '</div>')
    body += [hero_sheet(a, secrets) for a in heroes[1:]]
    body.append('<div class="chapter"><div class="head" data-run="SECRETOS DE LOS PROTAGONISTAS"><div class="num">APÉNDICE E</div><h1 id="secrets">Secretos de los protagonistas</h1><div class="sub">Entrégalos de uno en uno. Cada participante decide cuándo compartir el suyo.</div></div><div class="cols">' +
                ''.join(f'<h3>{a["name"]}</h3><blockquote><p>{html.escape(secrets[a["name"]])}</p></blockquote>' for a in heroes) + '</div></div>')
    body.append('<div class="chapter"><div class="head" data-run="DESAFÍOS Y AMENAZAS"><div class="num">APÉNDICE F</div><h1 id="stats">Desafíos y amenazas</h1><div class="sub">Un límite expresa una forma de superar la oposición, no puntos de golpe. Usa el estado que corresponda a la vía elegida.</div></div><div class="cols">' + stat_blocks(actors) + '</div></div>')
    pres = load('content/presentations.json')
    body.append('<div class="chapter"><div class="head" data-run="ROSTROS ANTE LA LÁMPARA"><div class="num">APÉNDICE G</div><h1 id="faces">Rostros ante la lámpara</h1><div class="sub">Lecturas de presentación. Léelas solo cuando esa persona entre en escena y adapta gestos, heridas y compañía a lo ocurrido.</div></div><div class="cols">' +
                ''.join(f'<h2>{html.escape(n)}</h2><blockquote>' + ''.join(f'<p>{p}</p>' for p in ps) + '</blockquote>' for n, ps in pres.items()) + '</div></div>')
    body.append('<div class="chapter"><div class="head" data-run="DOCUMENTOS PARA DESCUBRIR"><div class="num">APÉNDICE H</div><h1 id="docs">Documentos para descubrir</h1><div class="sub">Recorta y entrega solo la pieza encontrada.</div></div><div class="cols">' + doc_html(story, 'gm') + '</div></div>')
    body.append(closing_html())
    body.append(plate_html('scene-amanecer', 'Que ningún nombre se pierda', 'El Trono de la Sed', 'El sol encuentra las mismas piedras. Quienes regresan ya no las miran del mismo modo.'))
    book_chapters = chapters + [
        {'id': 'heroes', 'title': 'Los cinco protagonistas', 'num': 'Apéndice D', 'sections': []},
        {'id': 'secrets', 'title': 'Secretos de los protagonistas', 'num': 'Apéndice E', 'sections': []},
        {'id': 'stats', 'title': 'Desafíos y amenazas', 'num': 'Apéndice F', 'sections': []},
        {'id': 'faces', 'title': 'Rostros ante la lámpara', 'num': 'Apéndice G', 'sections': []},
        {'id': 'docs', 'title': 'Documentos para descubrir', 'num': 'Apéndice H', 'sections': []}]
    def doc(pages):
        return cover_html('Manual del Narrador') + front.replace('@@TOC@@', toc_html(book_chapters, pages)) + ''.join(body)
    pdf = render(doc(None), 'El-Trono-de-la-Sed-Manual')
    pdf = render(doc(locate(pdf, book_chapters)), 'El-Trono-de-la-Sed-Manual')
    return pdf

def build_players():
    chapters = [c for c in load_chapters(True) if c.get('audience') == 'players']
    story = load('content/narrative.json'); actors = load('content/actors.json'); secrets = load('content/personal-secrets.json')
    heroes = [a for a in actors if a['type'] == 'litm-character']; presentations = load('content/presentations.json')
    body = [cover_html('Cuaderno de protagonistas')]
    for c in chapters: body.append(chapter_html(c))
    body.append('<div class="chapter tight"><div class="head" data-run="PRIMERA IMPRESIÓN"><div class="num">PRESENTACIONES</div><h1>Primera impresión</h1></div><div class="cols">' +
                ''.join(f'<h2>{a["name"]}</h2><blockquote>' + ''.join(f'<p>{p}</p>' for p in presentations[a["name"]]) + '</blockquote>' for a in heroes) + '</div></div>')
    body += [hero_sheet(a, secrets) for a in heroes]
    body.append('<div class="chapter"><div class="head" data-run="COMPROMISO COMPARTIDO"><div class="num">LA COMPAÑÍA</div><h1>El compromiso compartido</h1></div><div class="cols">' + doc_html(story, 'players') + '</div></div>')
    return render(''.join(body), 'El-Trono-de-la-Sed-Material-de-Juego', 'CUADERNO DE PROTAGONISTAS')

if __name__ == '__main__':
    args = sys.argv[1:]
    if '--sync' in args: sync()
    if '--manual' in args or not args: print(build_manual())
    if '--players' in args or not args: print(build_players())
