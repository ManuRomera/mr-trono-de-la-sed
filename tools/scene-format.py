"""Exporta fondos 16:9; las láminas verticales editoriales conservan su propia copia."""
from pathlib import Path
from PIL import Image,ImageOps
import json,hashlib
root=Path(__file__).resolve().parents[1]
registry=json.loads((root/'docs/art-v3-assets.json').read_text());by_path={r['distributed']:r for r in registry}
for path in sorted((root/'assets/scenes').glob('*.webp')):
 slug=path.stem
 sources=[root/f'art/v4/empty/{slug}.png',root/f'art/v4/wide/{slug}.png']
 source=next((s for s in sources if s.exists()),None)
 if source is None and Image.open(path).size==(1920,1080):continue
 if source is None:source=path
 image=ImageOps.fit(Image.open(source).convert('RGB'),(1920,1080),method=Image.Resampling.LANCZOS)
 image.save(path,'WEBP',quality=93,method=6)
 record=by_path[str(path.relative_to(root))]
 if source!=path:record.update(source=str(source.relative_to(root)),sources=[str(source.relative_to(root))])
 record.update(width=1920,height=1080,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),use='Escena panorámica 16:9 · solo entorno, personajes mediante tokens')
for slug in ['corte','muhar','pozo']:
 path=root/f'assets/maps/{slug}-piedra.webp';source=root/f'art/v4/maps/{slug}.png'
 if not source.exists():continue
 image=ImageOps.fit(Image.open(source).convert('RGB'),(1920,1080),method=Image.Resampling.LANCZOS);image.save(path,'WEBP',quality=93,method=6)
 record=by_path[str(path.relative_to(root))];record.update(source=str(source.relative_to(root)),sources=[str(source.relative_to(root))],width=1920,height=1080,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),use='Plano 16:9 grabado en piedra · sin personajes')
(root/'docs/art-v3-assets.json').write_text(json.dumps(registry,ensure_ascii=False,indent=2)+'\n')
print('Escenas normalizadas a 1920 × 1080; fuentes editoriales independientes.')
