"""Banner y tarjeta social del repositorio con la marca MR (se parten de las capturas reales de Foundry).
Uso: python3 tools/readme_art.py [capturas/banquete.png]
"""
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
FONTS = root / 'editorial/fonts'
CIN = FONTS / 'cinzel/CinzelDecorative-Black.ttf'
CINB = FONTS / 'cinzel/CinzelDecorative-Bold.ttf'
GAR = FONTS / 'EBGaramond-Bold.ttf'
GARR = FONTS / 'EBGaramond-Regular.ttf'
GOLD, BONE, RUBY = (202, 166, 107), (245, 236, 215), (154, 63, 88)

def font(path, size): return ImageFont.truetype(str(path), size)

def tracked(d, xy, text, f, fill, tracking=0):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill); x += d.textlength(ch, font=f) + tracking
    return x

def cover_crop(src, size, focus=.97):
    w, h = size; im = src.convert('RGB'); s = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    top = int((im.height - h) * focus); return im.crop((0, top, w, top + h))

def veil(im, strength=235):
    w, h = im.size; g = Image.new('L', (w, h)); px = g.load()
    for x in range(w):
        a = max(0.0, 1 - x / (w * .78)) ** 1.25
        for y in range(h): px[x, y] = int(strength * a)
    dark = Image.new('RGB', (w, h), (11, 10, 16)); return Image.composite(dark, im, g)

def make(src_path, out, size):
    W, H = size; im = veil(cover_crop(Image.open(src_path), size)); d = ImageDraw.Draw(im)
    p = int(W * .045); y = int(H * .13)
    tracked(d, (p, y), 'UNA AVENTURA DE HORROR GÓTICO · LEGEND IN THE MIST', font(GAR, int(H * .034)), GOLD, int(H * .006))
    y += int(H * .10)
    tracked(d, (p, y), 'EL TRONO', font(CIN, int(H * .175)), BONE, int(H * .006)); y += int(H * .19)
    tracked(d, (p, y), 'DE LA SED', font(CIN, int(H * .175)), BONE, int(H * .006)); y += int(H * .215)
    d.rectangle((p, y, p + int(W * .08), y + 3), fill=RUBY); y += int(H * .045)
    d.text((p, y), 'La corte del rey sin nombre', font=font(CINB, int(H * .052)), fill=GOLD); y += int(H * .09)
    d.text((p, y), 'Un funeral sin nombre · seis personas desaparecidas · una balanza que pesa un juramento', font=font(GARR, int(H * .037)), fill=(222, 212, 190))
    logo = Image.open(root / 'brand/MR_11_Formal_Marfil_Transparente.png').convert('RGBA')
    lw = int(W * .15); logo = logo.resize((lw, int(lw * logo.height / logo.width)), Image.LANCZOS)
    im = im.convert('RGBA'); im.alpha_composite(logo, (W - lw - int(W * .035), int(H * .07)))
    out = Path(out); im = im.convert('RGB')
    if out.suffix == '.webp': im.save(out, 'WEBP', quality=88, method=6)
    else: im.save(out)
    print(out, im.size)

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else '/private/tmp/claude-501/-Volumes-Datos-Dock-FoundryVTT/6f29bf3d-cff6-403d-98f4-685e14273134/scratchpad/w/caps/banquete.png'
    make(src, root / 'docs/img/banner.webp', (1600, 560))
    make(src, root / 'docs/img/social.png', (1280, 640))
