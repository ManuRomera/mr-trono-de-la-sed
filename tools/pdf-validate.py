"""Auditoría de contenido y páginas; ignora cabeceras al comparar párrafos partidos."""
from pathlib import Path
import json,re,html,unicodedata
import fitz
root=Path(__file__).resolve().parents[1]
def sentences(t):
 t=re.sub('<[^>]+>','',html.unescape(t))
 return [x for x in re.split(r'(?<=[.!?:;»])\s+',t) if len(x.strip())>3]
def present(t,text):
 # Chrome intercala bloques al partir un párrafo entre columnas: se comprueban frases de cuatro palabras.
 w=re.sub('<[^>]+>','',html.unescape(t)).split()
 if len(w)<15:return norm(t) in text
 miss=[i for i in range(len(w)-3) if norm(' '.join(w[i:i+4])) not in text]
 return len(miss)<=6
def norm(t):return re.sub(r'[^\w]','',unicodedata.normalize('NFKC',html.unescape(re.sub('<[^>]+>','',t)))).lower()
def body(page):
 r=page.rect
 return page.get_text(clip=fitz.Rect(0,60,r.width,r.height-56))
manual=fitz.open(root/'output/pdf/El-Trono-de-la-Sed-Manual.pdf');players=fitz.open(root/'output/pdf/El-Trono-de-la-Sed-Material-de-Juego.pdf');text=norm(''.join(body(p) for p in manual));playertext=norm(''.join(body(p) for p in players));story=json.loads((root/'content/narrative.json').read_text());actors=json.loads((root/'content/actors.json').read_text());secrets=json.loads((root/'content/personal-secrets.json').read_text());missing=[];paragraphs=0
for ch in story['chapters']:
 if ch['audience']=='players':continue
 for sec in ch['sections']:
  for tag,t in re.findall(r'<(p|blockquote|li)\b[^>]*>(.*?)</\1>',sec['body'],re.S):
   paragraphs+=1
   if not present(t,text):missing.append(ch['id']+': '+sec['title']+' | '+re.sub('<[^>]+>','',t)[:40])
for handout in story['handouts']:
 target=playertext if handout.get('reveal')=='initial' else text
 for tag,t in re.findall(r'<(p|blockquote|li)\b[^>]*>(.*?)</\1>',handout['body'],re.S):
  if norm(t) not in target:missing.append('Ayuda: '+handout['id'])
for fig in story['figures']:
 for row in fig['rows']:
  for cell in row:
   if norm(cell) not in text:missing.append('Tabla: '+fig['id'])
for a in actors:
 if a['type']!='litm-character':continue
 targets=[t for _,t in re.findall(r'<(p|h3)\b[^>]*>(.*?)</\1>',a['system']['biography'],re.S)]
 for it in a['items']:
  s=it['system']
  if it['type']=='themebook':targets += [it['name'],s['quest']]+[t['name'] for t in s['powertags'] if not t.get('planned')]+[t['name'] for t in s['weaknesstags']]
  elif it['type']=='backpack':targets += [t['name'] for t in s.get('items',[])]
 for t in [x for x in targets if not x.startswith('Primera impresión')]:
  if not present(t,text) or not present(t,playertext):missing.append('Protagonista: '+a['name']+' / '+re.sub('<[^>]+>','',t)[:35])
 if norm(secrets[a['name']]) not in text:missing.append('Secreto: '+a['name'])
 if norm(secrets[a['name']]) in playertext:missing.append('Secreto filtrado al cuaderno: '+a['name'])
pages=[];empty=[];sparse=[]
for name,doc in [('Manual',manual),('Protagonistas',players)]:
 for i,page in enumerate(doc):
  r=page.rect;big=any(fitz.Rect(im['bbox']).width>=r.width*.98 and fitz.Rect(im['bbox']).height>=r.height*.98 for im in page.get_image_info())
  chars=[w for w in page.get_text('words') if 42<w[1] and w[3]<r.height-43]
  nchars=sum(len(w[4]) for w in chars)
  if nchars<20 and not big:empty.append(name+' '+str(i+1))
  if nchars<500 and not big:sparse.append(name+' '+str(i+1))
  pages.append({'book':name,'page':i+1,'content_characters':nchars,'full_page_art':big})
report={'narrative_paragraphs_checked':paragraphs,'missing_content':missing,'empty_content_pages':empty,'sparse_content_pages':sparse,'manual_pages':len(manual),'player_pages':len(players),'full_page_art_manual':[p['page'] for p in pages if p['book']=='Manual' and p['full_page_art']],'new_artworks':len({d['source'] for d in json.loads((root/'docs/art-v3-assets.json').read_text())}),'pages':pages}
(root/'docs/pdf-source-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='pages'},ensure_ascii=False));raise SystemExit(bool(missing or empty or sparse))
