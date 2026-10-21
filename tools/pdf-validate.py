"""Auditoría de contenido y páginas; ignora cabeceras al comparar párrafos partidos."""
from pathlib import Path
import json,re,html,unicodedata
import pdfplumber
from pypdf import PdfReader
root=Path(__file__).resolve().parents[1]
def norm(t):return re.sub(r'[^\w]','',unicodedata.normalize('NFKC',html.unescape(re.sub('<[^>]+>','',t)))).lower()
def body(page):
 t=page.extract_text() or ''
 if t.startswith('EL TRONO DE LA SED\n'):t='\n'.join(t.splitlines()[4:])
 return t
manual=PdfReader(root/'output/pdf/El-Trono-de-la-Sed-Manual.pdf');players=PdfReader(root/'output/pdf/El-Trono-de-la-Sed-Material-de-Juego.pdf');text=norm(''.join(body(p) for p in manual.pages));playertext=norm(''.join(body(p) for p in players.pages));story=json.loads((root/'content/narrative.json').read_text());actors=json.loads((root/'content/actors.json').read_text());secrets=json.loads((root/'content/personal-secrets.json').read_text());missing=[];paragraphs=0
for ch in story['chapters']:
 for sec in ch['sections']:
  for tag,t in re.findall(r'<(p|blockquote|li)\b[^>]*>(.*?)</\1>',sec['body'],re.S):
   paragraphs+=1
   if norm(t) not in text:missing.append(ch['id']+': '+sec['title'])
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
 for t in targets:
  if norm(t) not in text or norm(t) not in playertext:missing.append('Protagonista: '+a['name']+' / '+re.sub('<[^>]+>','',t)[:35])
 if norm(secrets[a['name']]) not in text:missing.append('Secreto: '+a['name'])
 if norm(secrets[a['name']]) in playertext:missing.append('Secreto filtrado al cuaderno: '+a['name'])
pages=[];empty=[]
for name,reader in [('Manual',manual),('Protagonistas',players)]:
 with pdfplumber.open(root/('output/pdf/El-Trono-de-la-Sed-'+('Manual' if name=='Manual' else 'Material-de-Juego')+'.pdf')) as doc:
  for i,page in enumerate(doc.pages):
   big=any(im['width']>=page.width*.98 and im['height']>=page.height*.98 for im in page.images)
   chars=[c for c in page.chars if 42<c['top'] and c['bottom']<page.height-43]
   if len(chars)<20 and not big:empty.append(name+' '+str(i+1))
   pages.append({'book':name,'page':i+1,'content_characters':len(chars),'full_page_art':big})
report={'narrative_paragraphs_checked':paragraphs,'missing_content':missing,'empty_content_pages':empty,'manual_pages':len(manual.pages),'player_pages':len(players.pages),'full_page_art_manual':[p['page'] for p in pages if p['book']=='Manual' and p['full_page_art']],'new_artworks':len({d['source'] for d in json.loads((root/'docs/art-v3-assets.json').read_text())}),'pages':pages}
(root/'docs/pdf-source-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='pages'},ensure_ascii=False));raise SystemExit(bool(missing or empty))
