"""Integra el arte de art/new: iconos de objetos, emblemas de desafíos, fondos de ayudas e iconos del módulo.
Idempotente. Uso: python3 tools/ingest_v16.py"""
from pathlib import Path
from PIL import Image, ImageDraw
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import brand
root = Path(__file__).resolve().parents[1]; NEW = root / 'art/new'
ITEMS = {'it-registro': 'registro-ofrendas', 'it-testimonio': 'testimonio-merit', 'it-cordon': 'cordon-zahra', 'it-lectura-nombre': 'lectura-nombre',
         'it-bendicion-umbral': 'bendicion-umbral', 'it-contrafirma': 'contrafirma', 'it-cofre': 'cofre-corazon'}
EMBLEMS = {'ac-funeral': 'funeral', 'ac-presion': 'presion', 'ac-registros': 'registros', 'ac-procesion': 'procesion', 'ac-banquete': 'banquete', 'ac-seduccion': 'seduccion',
           'ac-liberacion': 'liberacion', 'ac-pesaje': 'pesaje', 'ac-corazon': 'corazon', 'ac-coronacion': 'coronacion', 'ac-sacerdotes': 'sacerdotes', 'ac-huida': 'huida',
           'ac-camara-pesa': 'camara-pesa', 'ac-cincel': 'cincel', 'ac-caida': 'caida', 'ac-compania': 'compania'}
(root / 'assets/emblems').mkdir(exist_ok=True)
for k, slug in ITEMS.items():
    f = NEW / f'{k}.png'
    if not f.exists(): continue
    im = Image.open(f).convert('RGBA'); bb = im.getchannel('A').point(lambda v: 255 if v > 24 else 0).getbbox() or (0, 0, *im.size); im = im.crop(bb)
    S = 1024; s = min((S - 80) / im.width, (S - 80) / im.height); im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
    can = Image.new('RGBA', (S, S), (0, 0, 0, 0)); can.alpha_composite(im, ((S - im.width) // 2, (S - im.height) // 2))
    can.save(root / f'assets/objects/{slug}.webp', 'WEBP', quality=90, method=6, alpha_quality=100)
for k, slug in EMBLEMS.items():
    f = NEW / f'{k}.png'
    if not f.exists(): continue
    im = Image.open(f).convert('RGB').resize((768, 768), Image.LANCZOS)
    brand.corner(im.convert('RGBA'), .09, .5, .035).convert('RGB').save(root / f'assets/emblems/{slug}.webp', 'WEBP', quality=88, method=6)
# icono del módulo (macro, aventura)
mono = Image.open(root / 'brand/MR_09_Monograma_Marfil_Transparente.png').convert('RGBA'); mono = mono.crop(mono.getchannel('A').getbbox())
ic = Image.new('RGBA', (256, 256), (27, 36, 52, 255)); d = ImageDraw.Draw(ic); d.rounded_rectangle((6, 6, 249, 249), 38, outline=(202, 166, 107, 255), width=5)
w = 150; m = mono.resize((w, int(w * mono.height / mono.width)), Image.LANCZOS); ic.alpha_composite(m, ((256 - w) // 2, (256 - m.height) // 2))
ic.convert('RGB').save(root / 'assets/emblems/mr-icono.webp', 'WEBP', quality=90)
src = root / 'editorial/web/scene-neb-sekhem-2000.jpg'
if not src.exists(): src = root / 'assets/scenes/neb-sekhem.webp'
cv = Image.open(src).convert('RGB'); cv.thumbnail((900, 900)); cv.save(root / 'assets/emblems/portada.webp', 'WEBP', quality=86)
print('ok')
