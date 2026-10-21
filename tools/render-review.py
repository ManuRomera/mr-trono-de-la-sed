"""Renderiza cada página y verifica integridad y límites del texto de ambos PDF."""
from pathlib import Path
from pypdf import PdfReader
from PIL import Image,ImageDraw
import subprocess,shutil,json
root=Path(__file__).resolve().parents[1];reports=[]
try:import pdfplumber
except ImportError:pdfplumber=None
for pdf in sorted((root/'output/pdf').glob('*.pdf')):
 folder=root/'docs/previews'/('review-'+pdf.stem)
 if folder.exists():shutil.rmtree(folder)
 folder.mkdir(parents=True)
 subprocess.run(['pdftoppm','-scale-to','800','-png',str(pdf),str(folder/'page')],check=True,stdout=subprocess.DEVNULL)
 reader=PdfReader(pdf);files=sorted(folder.glob('page-*.png'));bad=[]
 if pdfplumber:
  with pdfplumber.open(pdf) as doc:
   for i,page in enumerate(doc.pages):
    clipped=[c.get('text') for c in page.chars if c['x0']<18 or c['x1']>page.width-18 or c['top']<5 or c['bottom']>page.height-5]
    if clipped:bad.append({'page':i+1,'text_outside_page':''.join(clipped)})
 thumbs=[]
 for f in files:
  im=Image.open(f).convert('RGB');im.thumbnail((178,252));thumbs.append(im)
 # Dividir vistas de conjunto para que cada página pueda inspeccionarse sin un lienzo enorme.
 for start in range(0,len(thumbs),24):
  group=thumbs[start:start+24];sheet=Image.new('RGB',(1068,276*((len(group)+5)//6)),'#aaa');draw=ImageDraw.Draw(sheet)
  for j,im in enumerate(group):x=j%6*178;y=j//6*276;sheet.paste(im,(x,y));draw.text((x+6,y+255),str(start+j+1),fill='black')
  sheet.save(folder/f'contact-{start//24+1}.jpg',quality=92)
 reports.append({'file':str(pdf.relative_to(root)),'pages':len(reader.pages),'rendered':len(files),'bytes':pdf.stat().st_size,'clipped_text':bad,'bounds_checked':bool(pdfplumber),'empty_text_pages':[i+1 for i,p in enumerate(reader.pages) if len((p.extract_text() or '').strip())<20]})
(root/'docs/pdf-review.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2));print(json.dumps(reports,ensure_ascii=False));raise SystemExit(any(r['clipped_text'] or r['empty_text_pages'] or r['pages']!=r['rendered'] for r in reports))
