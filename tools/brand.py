"""Marca MR en todas las imágenes distribuidas (escenas, mapas, láminas, retratos, fichas) y, muy disimulada, en la ropa de los tokens.

Idempotente: guarda el original en art/pristine (no se versiona) y siempre parte de él;
si el original no existe (clon limpio), docs/brand-applied.json evita marcar dos veces.
Uso:  python3 tools/brand.py [--force]
"""
from pathlib import Path
import base64, hashlib, json, re, shutil, sys
from PIL import Image

root = Path(__file__).resolve().parents[1]
PRIS = root / 'art/pristine'
LOG = root / 'docs/brand-applied.json'
LOGO = root / 'brand/MR_09_Monograma_Marfil_Transparente.png'
_logo = None

def logo():
    global _logo
    if _logo is None:
        im = Image.open(LOGO).convert('RGBA'); _logo = im.crop(im.getchannel('A').getbbox())
    return _logo

def stamp(im, width, alpha, pos):
    lg = logo(); w = max(16, int(width)); lg = lg.resize((w, int(w * lg.height / lg.width)), Image.LANCZOS)
    lg.putalpha(lg.getchannel('A').point(lambda v: int(v * alpha)))
    x, y = pos(lg.size); out = im.convert('RGBA'); out.alpha_composite(lg, (max(0, int(x)), max(0, int(y)))); return out

def corner(im, frac, alpha, margin=.018):
    w, h = im.size; m = int(min(w, h) * margin)
    return stamp(im, w * frac, alpha, lambda s: (w - s[0] - m, h - s[1] - m))

def on_clothing(im, frac=.03, alpha=.3):
    """Sello diminuto cosido en la ropa, hacia el bajo del traje: solo sobre píxeles opacos de la figura y
    con el tono contrario al del tejido para que apenas se note."""
    w, h = im.size; a = im.getchannel('A'); bb = a.point(lambda v: 255 if v > 30 else 0).getbbox() or (0, 0, w, h)
    lw = max(14, int(w * frac)); lg0 = logo(); lh = int(lw * lg0.height / lg0.width)
    ap = a.load(); fh = bb[3] - bb[1]; fw = bb[2] - bb[0]
    best = None
    for fy in (.80, .76, .72, .68, .84, .64):
        y = int(bb[1] + fh * fy)
        for fx in (.62, .66, .58, .70, .54, .74, .50, .78, .46):
            x = int(bb[0] + fw * fx)
            if x + lw >= w or y + lh >= h: continue
            if all(ap[x + i, y + j] >= 250 for i in range(0, lw, 3) for j in range(0, lh, 3)): best = (x, y); break
        if best: break
    if not best: best = (int(bb[0] + fw * .6), int(bb[1] + fh * .78))
    x, y = best; rgb = im.convert('RGB').crop((x, y, x + lw, y + lh)).resize((1, 1)).getpixel((0, 0))
    lum = .299 * rgb[0] + .587 * rgb[1] + .114 * rgb[2]
    src = Image.open(root / ('brand/MR_10_Monograma_Negro_Transparente.png' if lum > 135 else 'brand/MR_09_Monograma_Marfil_Transparente.png')).convert('RGBA')
    src = src.crop(src.getchannel('A').getbbox()).resize((lw, lh), Image.LANCZOS)
    mask = src.getchannel('A').point(lambda v: int(v * alpha)); src.putalpha(mask)
    out = im.convert('RGBA'); layer = Image.new('RGBA', out.size, (0, 0, 0, 0)); layer.alpha_composite(src, (x, y))
    # solo donde hay figura opaca
    la = layer.getchannel('A'); layer.putalpha(Image.composite(la, Image.new('L', la.size, 0), a.point(lambda v: 255 if v > 200 else 0)))
    out.alpha_composite(layer); return out

def targets():
    t = []
    t += [(p, lambda im: corner(im, .045, .45)) for p in sorted((root / 'assets/scenes').glob('*.webp'))]
    t += [(p, lambda im: corner(im, .045, .45)) for p in sorted((root / 'assets/maps').glob('*-piedra.webp'))]
    t += [(p, lambda im: corner(im, .05, .5)) for p in sorted((root / 'editorial/plates').glob('*.webp'))]
    t += [(p, lambda im: corner(im, .11, .55, .03)) for p in sorted(list((root / 'assets/npc').glob('*-portrait.webp')) + list((root / 'assets/characters').glob('*-portrait.webp')))]
    t += [(p, lambda im: corner(im, .05, .5)) for p in sorted((root / 'assets/characters').glob('*-sheet.webp'))]
    toks = list((root / 'assets/npc').glob('*-token.webp')) + list((root / 'assets/characters').glob('*-token.webp')) + [root / f'assets/objects/{n}.webp' for n in ('custodio', 'servidor', 'sombra-chacal')]
    t += [(p, on_clothing) for p in sorted(toks)]
    return t

def save(img, path):
    if img.getchannel('A').getextrema()[0] < 255:
        img.save(path, 'WEBP', quality=92, method=6, alpha_quality=100)
    else:
        img.convert('RGB').save(path, 'WEBP', quality=90, method=6)

def refresh_svg_aliases():
    """Los SVG de plano incrustan el WebP; se regeneran para que sigan coincidiendo."""
    for slug in ('corte', 'muhar', 'pozo'):
        svg = root / f'assets/maps/{slug}.svg'; webp = root / f'assets/maps/{slug}-piedra.webp'
        if not svg.exists() or not webp.exists(): continue
        data = base64.b64encode(webp.read_bytes()).decode()
        svg.write_text(re.sub(r'(data:image/webp;base64,)[A-Za-z0-9+/=]+', lambda m: m.group(1) + data, svg.read_text()))

def main(force=False):
    applied = json.loads(LOG.read_text()) if LOG.exists() else {}
    n = 0
    for path, fn in targets():
        rel = str(path.relative_to(root)); pr = PRIS / rel
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if not pr.exists():
            if applied.get(rel) == digest and not force: continue      # ya marcada y sin original: no repetir
            pr.parent.mkdir(parents=True, exist_ok=True); shutil.copy(path, pr)
        im = Image.open(pr); im.load()
        save(fn(im), path); applied[rel] = hashlib.sha256(path.read_bytes()).hexdigest(); n += 1
    refresh_svg_aliases()
    LOG.write_text(json.dumps(applied, indent=1, sort_keys=True))
    print('marcadas', n, 'imágenes;', len(applied), 'registradas')

if __name__ == '__main__':
    main('--force' in sys.argv)
