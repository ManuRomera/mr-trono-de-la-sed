"""Compone las ayudas como imágenes: fondo generado (art/new/dc-*.png, sin texto) + el texto real del manual.
El texto sale de content/narrative.json (una sola fuente) y se ajusta a la zona de escritura de cada fondo.
Uso: python3 tools/handouts.py [--pdf]   -> assets/handouts/<id>.webp  (+ output/pdf/…-Ayudas-de-juego.pdf)"""
from pathlib import Path
import json, re, sys, html
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
sys.path.insert(0, str(Path(__file__).resolve().parent))
import brand
root = Path(__file__).resolve().parents[1]; NEW = root / 'art/new'; OUT = root / 'assets/handouts'; OUT.mkdir(exist_ok=True)
F = root / 'editorial/fonts'
FONTS = {'it': F / 'EBGaramond-Italic.ttf', 'rg': F / 'EBGaramond-Regular.ttf', 'bd': F / 'EBGaramond-Bold.ttf', 'cin': F / 'cinzel/CinzelDecorative-Regular.ttf'}
# bg: fondo; box: zona de escritura (fracciones x0,y0,x1,y1); ink: color de tinta; font; align; title: muestra el título; rot: giro leve (grados)
CFG = json.loads((root / 'content/handouts.json').read_text())

def paragraphs(body):
    out = []
    for tag, t in re.findall(r'<(p|li|h3)\b[^>]*>(.*?)</\1>', body, re.S):
        t = html.unescape(re.sub(r'<br\s*/?>', '\n', re.sub(r'</?(b|i|em|strong)>', '', t))); t = re.sub(r'<[^>]+>', '', t).strip()
        if t: out.append((tag, t))
    return out

def wrap(d, text, font, width):
    lines = []
    for raw in text.split('\n'):
        cur = ''
        for w in raw.split(' '):
            trial = (cur + ' ' + w).strip()
            if d.textlength(trial, font=font) <= width or not cur: cur = trial
            else: lines.append(cur); cur = w
        lines.append(cur)
    return lines

def fit(paras, box_w, box_h, fontfile, title=None, maxsize=64, spacing=1.36):
    d = ImageDraw.Draw(Image.new('L', (8, 8)))
    for size in range(maxsize, 14, -1):
        font = ImageFont.truetype(str(fontfile), size); h = 0; laid = []
        if title:
            tf = ImageFont.truetype(str(FONTS['cin']), int(size * .82)); tl = wrap(d, title.upper(), tf, box_w); laid.append(('title', tf, tl)); h += len(tl) * tf.size * 1.3 + size * .7
        for tag, t in paras:
            lines = wrap(d, t, font, box_w); laid.append(('p', font, lines)); h += len(lines) * size * spacing + size * .5
        if h <= box_h: return laid, size
    return laid, size

def compose(h, cfg, title):
    bg = Image.open(NEW / f"{cfg['bg']}.png").convert('RGB'); W, H = bg.size
    x0, y0, x1, y1 = cfg['box']; bw, bh = int((x1 - x0) * W), int((y1 - y0) * H)
    fontfile = FONTS[cfg.get('font', 'it')]
    paras = paragraphs(h['body']); laid, size = fit(paras, bw, bh, fontfile, title if cfg.get('title') else None, maxsize=int(W * .06))
    mask = Image.new('L', (bw, bh), 0); d = ImageDraw.Draw(mask)
    total = sum((len(l) * f.size * (1.3 if k == 'title' else 1.36)) + (f.size * (.7 if k == 'title' else .5)) for k, f, l in laid)
    y = 0 if cfg.get('valign', 'top') == 'top' else max(0, (bh - total) / 2)
    for k, f, lines in laid:
        for ln in lines:
            w = d.textlength(ln, font=f); x = 0 if (cfg.get('align', 'left') == 'left' and k != 'title') else (bw - w) / 2
            d.text((x, y), ln, font=f, fill=255); y += f.size * (1.3 if k == 'title' else 1.36)
        y += f.size * (.7 if k == 'title' else .5)
    rot = cfg.get('rot', 0)
    if rot: mask = mask.rotate(rot, resample=Image.BICUBIC, expand=True)
    mask = mask.filter(ImageFilter.GaussianBlur(.7))
    ink = Image.new('RGB', mask.size, tuple(cfg.get('ink', (42, 29, 18))))
    layer = bg.copy(); alpha = mask.point(lambda v: int(v * cfg.get('alpha', .9)))
    px = int(x0 * W - (mask.width - bw) / 2); py = int(y0 * H - (mask.height - bh) / 2)
    region = layer.crop((px, py, px + mask.width, py + mask.height))
    # tinta multiplicada sobre el soporte: toma su textura
    inked = ImageChops.multiply(region, Image.composite(ink, Image.new('RGB', mask.size, (255, 255, 255)), alpha)) if cfg.get('multiply', True) else Image.composite(ink, region, alpha)
    layer.paste(inked, (px, py))
    return layer

def main(make_pdf=False):
    story = json.loads((root / 'content/narrative.json').read_text()); made = []
    for h in story['handouts']:
        cfg = CFG.get(h['id'])
        if not cfg or not (NEW / f"{cfg['bg']}.png").exists(): continue
        im = compose(h, cfg, h['title']) if cfg.get('text', True) else Image.open(NEW / f"{cfg['bg']}.png").convert('RGB')
        im = brand.corner(im.convert('RGBA'), .05, .4, .02).convert('RGB'); im.thumbnail((1600, 1600), Image.LANCZOS)
        im.save(OUT / f"{h['id']}.webp", 'WEBP', quality=88, method=6); made.append((h['id'], h['title']))
    print('ayudas:', len(made))
    if make_pdf and made:
        import fitz
        doc = fitz.open(); 
        for hid, title in made:
            im = Image.open(OUT / f'{hid}.webp').convert('RGB'); r = fitz.Rect(0, 0, 595.3, 841.9); page = doc.new_page(width=595.3, height=841.9)
            page.draw_rect(r, color=None, fill=(.965, .941, .89))
            s = min((r.width - 60) / im.width, (r.height - 110) / im.height); w, hh = im.width * s, im.height * s
            rect = fitz.Rect((r.width - w) / 2, 70, (r.width + w) / 2, 70 + hh)
            tmp = OUT / f'_tmp_{hid}.jpg'; im.save(tmp, quality=92); page.insert_image(rect, filename=str(tmp)); tmp.unlink()
            page.insert_text((30, 40), 'EL TRONO DE LA SED · AYUDA PARA ENTREGAR', fontsize=8, color=(.44, .2, .28)); page.insert_text((30, 54), title, fontsize=13, color=(.15, .13, .17))
            page.insert_text((30, 820), 'MR · Manu Romera · Digital RPG Design · Recorta y entrega solo la pieza encontrada.', fontsize=7, color=(.5, .45, .4))
        doc.save(root / 'output/pdf/El-Trono-de-la-Sed-Ayudas-de-Juego.pdf', deflate=True)
        print('pdf ok')

if __name__ == '__main__': main('--pdf' in sys.argv)
