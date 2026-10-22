"""Miniaturas de escena (400 px) para el selector de escenas de Foundry: assets/thumbs/<slug>.webp.
Uso: python3 tools/thumbs.py"""
from pathlib import Path
from PIL import Image
root = Path(__file__).resolve().parents[1]
out = root / 'assets/thumbs'; out.mkdir(exist_ok=True)
sources = {p.stem: p for p in (root / 'assets/scenes').glob('*.webp')}
for slug in ('corte', 'muhar', 'pozo'):
    sources['map-' + slug if slug != 'corte' else 'corte'] = root / f'assets/maps/{slug}-piedra.webp'
n = 0
for slug, src in sources.items():
    im = Image.open(src).convert('RGB'); im.thumbnail((400, 400), Image.LANCZOS)
    im.save(out / f'{slug}.webp', 'WEBP', quality=80, method=6); n += 1
print('miniaturas:', n)
