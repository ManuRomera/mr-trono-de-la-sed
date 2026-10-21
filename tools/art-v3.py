"""Exporta la colección dibujada: maestros, tokens alfa y fondos de ficha nativos.

Los recortes y la composición son variantes del mismo arte generado; no se
sustituye el dibujo por filtros ni se pinta sobre los maestros.
"""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1]
STAGE=ROOT/'art/v3/masters'
HEROES=['zahra','khaem','neset','seneb','iru']
NPCS=['merit','khety','tia','panehsy','nefru','serekh','neb-sekhem','hori','paser','tamerit','kasa','beset','dedi','henut']
# Coordenadas revisadas sobre maestros 1024x1536; rostro y coronilla dentro del recorte.
FACES={'zahra':(340,0,740,400),'khaem':(330,0,730,400),'neset':(330,0,730,400),'seneb':(330,0,730,400),'iru':(300,0,700,400)}
REG=[]
def source(slug):return ROOT/f'art/masters/{slug}.png'
def save(im,path,masters,use,alpha=False):
 p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
 im.save(p,'WEBP',quality=94,lossless=alpha,method=6)
 REG.append(dict(distributed=path,sources=[f'art/masters/{m}.png' for m in masters],source=f'art/masters/{masters[0]}.png',use=use,width=im.width,height=im.height,bytes=p.stat().st_size,alpha=alpha,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
def rgba(slug):return Image.open(source(slug)).convert('RGBA')
def cutout(im,size=1024):
 # Alfa nativo conservado íntegro. El margen evita cortar pies, manos o armas.
 canvas=Image.new('RGBA',(size,size));body=ImageOps.contain(im,(size-100,size-100),Image.Resampling.LANCZOS)
 canvas.alpha_composite(body,((size-body.width)//2,(size-body.height)//2));return canvas

def portrait(slug):
 im=rgba(slug);box=FACES.get(slug,(300,0,740,440));im=im.crop(box)
 canvas=Image.new('RGBA',im.size,'#273447');canvas.alpha_composite(im)
 return canvas.convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
def sheet(slug):
 scene=Image.open(source(slug+'-sheet-background')).convert('RGB');w,h=scene.size
 # Se usa el tramo del entorno sin la figura del fondo generado. El personaje
 # canónico se compone a escala con el rostro en la guía izquierda del sistema.
 scene=scene.crop((int(w*.57),0,w,h));bg=ImageOps.fit(scene,(1100,800),Image.Resampling.LANCZOS).convert('RGBA')
 shade=Image.new('RGBA',bg.size,(12,20,32,65));bg.alpha_composite(shade)
 im=rgba(slug);scale=.56;im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
 box=FACES[slug];face_x=(box[0]+box[2])/2;bg.alpha_composite(im,(round(150-face_x*scale),65))
 # Oscurecer suavemente debajo del nombre nativo; sin texto ni tarjetas pintadas.
 fade=Image.new('RGBA',bg.size);pixels=fade.load()
 for y in range(800):
  a=round(205*max(0,min(1,(y-440)/280)))
  for x in range(1100):pixels[x,y]=(10,17,27,a)
 bg.alpha_composite(fade)
 return bg.convert('RGB')

def main():
 original={p.stem for p in (ROOT/'art/archive/v0.2.1/masters').glob('*.png')}
 expected=original|{f'npc-{n}' for n in NPCS}|{f'{h}-sheet-background' for h in HEROES}|{'scene-neb-sekhem','scene-coronacion'}
 missing=expected-{p.stem for p in STAGE.glob('*.png')}
 if missing:raise ValueError('Faltan maestros: '+', '.join(sorted(missing)))
 for slug in sorted(expected):shutil.copy2(STAGE/(slug+'.png'),source(slug))
 for slug in HEROES:
  save(portrait(slug),f'assets/characters/{slug}-portrait.webp',[slug],'Compacto y listados')
  save(cutout(rgba(slug)),f'assets/characters/{slug}-token.webp',[slug],'Token: cuerpo entero sin fondo ni marco',True)
  save(sheet(slug),f'assets/characters/{slug}-sheet.webp',[slug,slug+'-sheet-background'],'Ficha amplia nativa, guía de identidad x=300')
 for slug in NPCS:
  master='npc-'+slug;pr=portrait(master)
  save(pr,f'assets/npc/{slug}-portrait.webp',[master],'Retrato compacto')
  save(pr.resize((110,110),Image.Resampling.LANCZOS),f'assets/npc/{slug}-thumb.webp',[master],'Miniatura')
  save(cutout(rgba(master)),f'assets/npc/{slug}-token.webp',[master],'Token: cuerpo entero sin fondo ni marco',True)
 objects=['arpa','corazon','escarabajo','invitacion','pluma']+['vasija-'+s for s in ['hori','paser','tamerit','kasa','beset','dedi','septima']]
 creatures=['custodio','servidor','sombra-chacal']
 for slug in objects+creatures:
  im=rgba(slug);im=cutout(im,1024) if slug in creatures else ImageOps.contain(im,(512,512),Image.Resampling.LANCZOS)
  save(im,f'assets/objects/{slug}.webp',[slug],'Criatura completa transparente' if slug in creatures else 'Objeto de juego',True)
 for slug in sorted(expected-set(HEROES)-{'npc-'+s for s in NPCS}-{s+'-sheet-background' for s in HEROES}-set(objects+creatures)):
  if slug.startswith('mapa-'):
   path=f'assets/maps/{slug.removeprefix("mapa-")}.webp'
  else:path=f'assets/scenes/{slug.removeprefix("scene-")}.webp'
  save(Image.open(source(slug)).convert('RGB'),path,[slug],'Mapa grabado frontal' if slug.startswith('mapa-') else 'Ilustración narrativa')
 (ROOT/'docs/art-v3-assets.json').write_text(json.dumps(REG,ensure_ascii=False,indent=2))
 manifest=[]
 for slug in sorted(expected):
  job=json.loads((ROOT/f'art/v3/jobs/{slug}.json').read_text());im=Image.open(source(slug));job.update(master=f'art/masters/{slug}.png',width=im.width,height=im.height,sha256=hashlib.sha256(source(slug).read_bytes()).hexdigest(),status='reviewed-and-integrated',variants=[r['distributed'] for r in REG if f'art/masters/{slug}.png' in r['sources']]);manifest.append(job)
 (ROOT/'art/v3/inventory.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 print(f'{len(expected)} maestros; {len(REG)} WebP derivados')
if __name__=='__main__':main()

# Los fondos de juego usan las revisiones panorámicas sin personajes.
import runpy
runpy.run_path(str(ROOT/'tools/scene-format.py'))
