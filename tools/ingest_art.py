"""Convierte el arte nuevo de art/new en tokens, retratos, miniaturas y láminas del módulo.
Uso: python3 tools/ingest_art.py   (idempotente; después, tools/brand.py estampa la marca)"""
from pathlib import Path
from PIL import Image
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import brand
root = Path(__file__).resolve().parents[1]
NEW = root / 'art/new'
CREATURES = {'borrado': 'borrado', 'plañidera': 'planidera', 'pesador': 'pesador'}
PLATES = {'lamina-borrados': 'editorial/plates/lamina-borrados.webp', 'lamina-dios': 'editorial/plates/lamina-dios.webp'}

def token(src, dst_slug):
    im = Image.open(src).convert('RGBA'); bb = im.getchannel('A').point(lambda v: 255 if v > 30 else 0).getbbox(); fig = im.crop(bb)
    S = 1024; inner = S - 2 * 56; s = min(inner / fig.width, inner / fig.height)
    fig = fig.resize((max(1, round(fig.width * s)), max(1, round(fig.height * s))), Image.LANCZOS)
    can = Image.new('RGBA', (S, S), (0, 0, 0, 0)); can.alpha_composite(fig, ((S - fig.width) // 2, S - 56 - fig.height))
    pristine = root / 'art/pristine/assets/npc' / f'{dst_slug}-token.webp'; pristine.parent.mkdir(parents=True, exist_ok=True)
    can.save(pristine, 'WEBP', quality=92, method=6, alpha_quality=100)
    marked = brand.on_clothing(can)
    out = root / 'assets/npc' / f'{dst_slug}-token.webp'; marked.save(out, 'WEBP', quality=92, method=6, alpha_quality=100)
    # retrato y miniatura sobre fondo de noche
    head = can.crop((can.width // 2 - 260, 40, can.width // 2 + 260, 560)); bg = Image.new('RGBA', head.size, (27, 36, 52, 255)); bg.alpha_composite(head)
    por = bg.convert('RGB').resize((512, 512), Image.LANCZOS)
    por = brand.corner(por.convert('RGBA'), .11, .55, .03).convert('RGB'); por.save(root / 'assets/npc' / f'{dst_slug}-portrait.webp', 'WEBP', quality=88)
    por.resize((110, 110), Image.LANCZOS).save(root / 'assets/npc' / f'{dst_slug}-thumb.webp', 'WEBP', quality=88)

for k, slug in CREATURES.items():
    if (NEW / f'{k}.png').exists(): token(NEW / f'{k}.png', slug)
for k, dst in PLATES.items():
    if (NEW / f'{k}.png').exists():
        im = Image.open(NEW / f'{k}.png').convert('RGB'); out = root / dst; out.parent.mkdir(exist_ok=True)
        brand.corner(im.convert('RGBA'), .05, .5).convert('RGB').save(out, 'WEBP', quality=90, method=6)
print('ok')
