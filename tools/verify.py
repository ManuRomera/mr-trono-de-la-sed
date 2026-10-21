"""Comprueba coherencia de fuentes, documentos y rutas antes de empaquetar."""
from pathlib import Path
import json,re,hashlib,base64,xml.etree.ElementTree as ET
from PIL import Image
root=Path(__file__).resolve().parents[1];mod='mr-trono-de-la-sed';prefix='modules/'+mod+'/'
def read(p):return json.loads((root/p).read_text())
adv=read('_data/aventura.json')[0];errors=[];references={}
def visit(x,owner):
 if isinstance(x,dict):
  for k,v in x.items():visit(v,owner)
 elif isinstance(x,list):
  for v in x:visit(v,owner)
 elif isinstance(x,str):
  for ref in re.findall(re.escape(prefix)+r'[^\s\"<>\]\)]+',x):
   p=ref[len(prefix):];references.setdefault(p,set()).add(owner)
   if not (root/p).is_file():errors.append('Recurso ausente: '+p)
for collection in ['actors','items','journal','scenes','macros','playlists']:
 ids=[]
 for d in adv.get(collection,[]):
  ids.append(d['_id']);visit(d,collection+':'+d['name'])
  if not re.fullmatch('[a-zA-Z0-9]{16}',d['_id']):errors.append('ID no válido: '+d['name'])
 if len(ids)!=len(set(ids)):errors.append('IDs repetidos '+collection)
heroes=[a for a in adv['actors'] if a['type']=='litm-character']
if len(heroes)!=5:errors.append('Deben existir cinco héroes')
for a in heroes:
 themes=[i for i in a['items'] if i['type']=='themebook']
 if len(themes)!=4:errors.append(a['name']+': temas incorrectos')
 for t in themes:
  if len([p for p in t['system']['powertags'] if not p.get('planned')])!=3 or len(t['system']['weaknesstags'])!=1:errors.append(t['name']+': etiquetas iniciales incorrectas')
 if len([i for i in a['items'] if i['type']=='backpack'])!=1:errors.append(a['name']+': mochila duplicada/ausente')
 shared=next((s for s in adv['actors'] if s['_id']==a['system']['actorSharedSingleThemecardId']),None)
 if not shared or shared['type']!='litm-fellowship-themecard' or shared['ownership'].get('default')!=3:errors.append(a['name']+': compañía no funcional')
# Los antiguos mapas SVG son alias con WebP incrustado: siguen funcionando tras actualizar.
for slug in ['corte','muhar','pozo']:
 alias=root/f'assets/maps/{slug}.svg';image=root/f'assets/maps/{slug}-piedra.webp'
 try:
  node=ET.fromstring(alias.read_text()).find('{http://www.w3.org/2000/svg}image')
  encoded=node.attrib['href'].split('data:image/webp;base64,',1)[1]
  if base64.b64decode(encoded)!=image.read_bytes():errors.append('Alias desactualizado: '+slug)
  references.setdefault(str(image.relative_to(root)),set()).add('Mapa grabado incrustado: '+slug)
 except (ValueError,KeyError,AttributeError,FileNotFoundError,ET.ParseError):errors.append('Alias de mapa no válido: '+slug)
derivatives={d['distributed']:d for d in read('docs/art-v3-assets.json')}
audio_index={d['path']:d for d in read('content/audio.json')}
# Cada escena tiene lectura privada y vínculos nativos de música válidos.
by_journal={j['_id']:j for j in adv['journal']};by_playlist={p['_id']:p for p in adv['playlists']}
for scene in adv['scenes']:
 guide=by_journal.get(scene.get('journal'));pl=by_playlist.get(scene.get('playlist'))
 if not guide or guide['ownership'].get('default')!=0:errors.append('Lectura no privada o ausente: '+scene['name'])
 elif '<blockquote>' not in guide['pages'][0]['text']['content']:errors.append('Lectura vacía: '+scene['name'])
 if not pl or scene.get('playlistSound') not in {s['_id'] for s in pl['sounds']}:errors.append('Música no enlazada: '+scene['name'])
assets=[]
# El inventario global deriva usos de los documentos: no mantiene rutas de uso a mano.
for p in sorted((root/'assets').rglob('*')):
 if not p.is_file():continue
 rel=str(p.relative_to(root));entry={'distributed':rel,'format':p.suffix[1:],'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'documents':sorted(references.get(rel,[]))}
 if p.suffix.lower() in ['.webp','.png','.jpg','.jpeg']:
  im=Image.open(p);im.verify();im=Image.open(p);entry.update(width=im.width,height=im.height)
  possible=[root/'art/masters'/f'{p.stem}.png',root/'art/masters'/f'scene-{p.stem}.png']
  if '/characters/' in rel:possible.insert(0,root/'art/masters'/(p.stem.split('-')[0]+'.png'))
  if '/maps/' in rel:possible.insert(0,root/'art/masters'/('mapa-'+p.stem+'.png'))
  if '/npc/' in rel:possible.insert(0,root/'art/masters'/('npc-'+p.stem.split('-')[0]+'.png'))
  entry['source']=next((str(s.relative_to(root)) for s in possible if s.exists()),None)
 if rel in derivatives:entry.update(source=derivatives[rel]['source'],sources=derivatives[rel]['sources'],use=derivatives[rel]['use'])
 if '/maps/' in rel and p.suffix=='.svg':entry.update(source=f'art/masters/mapa-{p.stem}-piedra.png',embedded=f'assets/maps/{p.stem}-piedra.webp',legacy_path_preserved=True)
 if rel in audio_index:entry.update(audio_index[rel])
 assets.append(entry)
for path in ['js/main.mjs','js/private-store.mjs','js/state.mjs','styles/trono.css','tours/narrator.json','tours/players.json','lang/es.json','lang/en.json']:
 if not (root/path).exists():errors.append('Archivo necesario ausente '+path)
(root/'docs/assets-inventory.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2))
report={'status':'pass' if not errors else 'fail','errors':errors,'counts':{k:len(adv.get(k,[])) for k in ['actors','items','journal','scenes','macros','playlists']},'assets':len(assets),'asset_bytes':sum(a['bytes'] for a in assets),'image_references':len(references),'missing':len(errors),'runtime_evidence':['foundry-direction-v1.json','audio-validation.json','pdf-review.json','pdf-source-coverage.json'],'release_status':'1.0.0, publication authorized by author','pending':['Verificación editorial de dobles páginas de impresión a mayor resolución','Prueba de mesa con 4–5 personas']}
(root/'docs/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False));raise SystemExit(bool(errors))
