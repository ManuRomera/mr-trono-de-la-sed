"""Edición local A4: texto continuo, láminas, fichas y ayudas desde las fuentes comunes."""
from pathlib import Path
import json,re,html,math
from PIL import Image as PILImage
from reportlab.platypus import (BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,PageBreak,NextPageTemplate,Image,KeepTogether,Table,TableStyle,Flowable,CondPageBreak)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor,Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.tableofcontents import TableOfContents
root=Path(__file__).resolve().parents[1];out=root/'output/pdf';out.mkdir(parents=True,exist_ok=True)
cache=root/'editorial/cache';cache.mkdir(parents=True,exist_ok=True)
for n,f in [('Body','Regular'),('BodyBold','Bold'),('BodyItalic','Italic')]:pdfmetrics.registerFont(TTFont(n,str(root/f'editorial/fonts/EBGaramond-{f}.ttf')))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='BodyItalic',boldItalic='BodyBold')
W,H=595.276,841.89;M=40;CW=(W-2*M-22)/2;PW=W-2*M;FH=H-100
INK=HexColor('#25242b');RUBY=HexColor('#713447');GOLD=HexColor('#a78850');PAPER=HexColor('#f6f0e3');BLUE=HexColor('#1b2434')
styles={
 'body':ParagraphStyle('body',fontName='Body',fontSize=11.2,leading=14.2,spaceAfter=6,textColor=INK,allowWidows=0,allowOrphans=0),
 'h1':ParagraphStyle('h1',fontName='BodyBold',fontSize=21,leading=24,spaceBefore=15,spaceAfter=13,textColor=RUBY,keepWithNext=True),
 'h2':ParagraphStyle('h2',fontName='BodyBold',fontSize=13.4,leading=15.7,spaceBefore=9,spaceAfter=5,textColor=RUBY,keepWithNext=True),
 'quote':ParagraphStyle('quote',fontName='BodyItalic',fontSize=11.3,leading=14.8,spaceBefore=7,spaceAfter=10,leftIndent=10,rightIndent=7,borderColor=GOLD,borderWidth=.5,borderPadding=7,backColor=HexColor('#e9dfcc')),
 'small':ParagraphStyle('small',fontName='Body',fontSize=10,leading=12.3,spaceAfter=5,textColor=INK),
 'caption':ParagraphStyle('caption',fontName='BodyItalic',fontSize=9.5,leading=11.4,spaceAfter=8,textColor=HexColor('#645646')),
 'hero':ParagraphStyle('hero',fontName='Body',fontSize=10.8,leading=12.8,spaceAfter=5,textColor=INK),
 'theme':ParagraphStyle('theme',fontName='Body',fontSize=10.8,leading=12.8,spaceAfter=4,textColor=INK),
 'themehead':ParagraphStyle('themehead',fontName='BodyBold',fontSize=12.6,leading=14.5,spaceAfter=7,textColor=RUBY),
 'handout':ParagraphStyle('handout',fontName='Body',fontSize=11.9,leading=15,spaceAfter=7,textColor=INK),
}
def p(t,s='body'):return Paragraph(re.sub(r'<br\s*/?>','<br/>',t,flags=re.I),styles[s])
def esc(t):return html.escape(str(t))
def blocks(source,style='body',compact=False):
 if compact:source=re.sub(r'<h3>(.*?)</h3>\s*<p>',r'<p><b>\1.</b> ',source,flags=re.S)
 result=[]
 for tag,body in re.findall(r'<(p|blockquote|h3|ul|ol)\b[^>]*>(.*?)</\1>',source,re.S):
  if tag in ('ul','ol'):result.extend(p('• '+x,style) for x in re.findall(r'<li>(.*?)</li>',body,re.S))
  else:result.append(p(body,'quote' if tag=='blockquote' else 'h2' if tag=='h3' else style))
 return result or [p(re.sub('<[^>]+>','',source),style)]
def jpeg(path):
 path=Path(path);dest=cache/(path.stem+'.jpg')
 if not dest.exists() or dest.stat().st_mtime<path.stat().st_mtime:
  im=PILImage.open(path).convert('RGBA');bg=PILImage.new('RGBA',im.size,'#f6f0e3');bg.alpha_composite(im);im=bg.convert('RGB');im.thumbnail((2200,3000));im.save(dest,quality=93,subsampling=0)
 return str(dest)
def artpath(name):
 path=root/f'art/masters/{name}.png'
 if path.exists():return path
 # La copia pública reconstruye el PDF con los WebP distribuidos; los PNG
 # maestros de producción permanecen en el proyecto del autor.
 candidates=[root/f'assets/scenes/{name.removeprefix("scene-")}.webp',root/f'assets/objects/{name}.webp']
 if name.startswith('mapa-'):candidates.insert(0,root/f'assets/maps/{name.removeprefix("mapa-")}.webp')
 if name in ['zahra','khaem','neset','seneb','iru']:candidates.insert(0,root/f'assets/characters/{name}-token.webp')
 selected=next((p for p in candidates if p.exists()),None)
 if not selected:raise FileNotFoundError(path)
 if name in ['zahra','khaem','neset','seneb','iru']:
  target=cache/('source-'+name+'.png');im=PILImage.open(selected).convert('RGBA');box=im.getchannel('A').point(lambda p:255 if p>32 else 0).getbbox();im.crop(box).save(target);return target
 return selected
class Rule(Flowable):
 def __init__(self):super().__init__();self.height=8
 def draw(self):self.canv.setStrokeColor(GOLD);self.canv.setLineWidth(.5);self.canv.line(0,4,self._frame._aW if hasattr(self,'_frame') else CW,4)
class Plate(Flowable):
 def __init__(self,art,title,kicker='',quote='',cover=False,toc=None):super().__init__();self.art=art;self.title=title;self.kicker=kicker;self.quote=quote;self.cover=cover;self.toc=toc;self.height=1
 def draw(self):
  c=self.canv;c.saveState();c.resetTransforms();file=jpeg(artpath(self.art));im=PILImage.open(file);iw,ih=im.size;s=max(W/iw,H/ih)
  c.drawImage(file,(W-iw*s)/2,(H-ih*s)/2,iw*s,ih*s)
  # Una sola veladura de tinta: evita bandas visibles en visores PDF.
  c.setFillColor(Color(.055,.075,.12,alpha=.82));c.rect(0,0,W,0 if self.cover else 225,fill=1,stroke=0)
  if self.cover:
   import runpy
   runpy.run_path(str(root/'tools/cover-v4.py'))['cover'](c,W,H,'Manual del Narrador' if 'Manual' in self.kicker else 'Cuaderno de protagonistas')
  else:
   c.setFont('BodyBold',10);c.setFillColor(HexColor('#d4b776'));c.drawString(M,205,self.kicker.upper())
   title=Paragraph(self.title,ParagraphStyle('plate',fontName='BodyBold',fontSize=34,leading=36,textColor=PAPER));_,th=title.wrap(PW,120);title.drawOn(c,M,190-th)
   if self.quote:
    q=Paragraph(self.quote,ParagraphStyle('platequote',fontName='BodyItalic',fontSize=13,leading=17,textColor=PAPER));_,qh=q.wrap(PW-10,80);q.drawOn(c,M,54)
   c.setFont('Body',8);c.setFillColor(PAPER);c.drawRightString(W-M,25,str(c.getPageNumber()))
  c.restoreState()
class Coda(Flowable):
 """Recuadro de consulta en la columna libre al cerrar una parte, sin crear páginas."""
 def __init__(self,icon,title,text,quote):super().__init__();self.icon=icon;self.title=title;self.text=text;self.quote=quote;self.height=1
 def wrap(self,aw,ah):self.remaining=ah;return aw,1
 def draw(self):
  frame=self._doctemplate.frame;c=self.canv
  if frame.id=='left':x=M+CW+22;y=48;h=FH
  elif self.remaining>=350:x=M+CW+22;y=48;h=self.remaining-3
  else:return
  c.saveState();c.resetTransforms();c.setFillColor(BLUE);c.rect(x,y,CW,h,fill=1,stroke=0);c.setStrokeColor(GOLD);c.rect(x+8,y+8,CW-16,h-16,fill=0,stroke=1)
  title=Paragraph(self.title,ParagraphStyle('codah',fontName='BodyBold',fontSize=19,leading=22,textColor=HexColor('#d9bd81')));_,th=title.wrap(CW-40,300);title.drawOn(c,x+20,y+h-24-th)
  text=Paragraph(self.text,ParagraphStyle('codat',fontName='Body',fontSize=11.5,leading=15,textColor=PAPER));_,bh=text.wrap(CW-40,700);text.drawOn(c,x+20,y+h-40-th-bh)
  q=Paragraph(self.quote,ParagraphStyle('codaq',fontName='BodyItalic',fontSize=12,leading=16,textColor=HexColor('#d9bd81')));_,qh=q.wrap(CW-40,200);q.drawOn(c,x+20,y+25)
  available=h-90-th-bh-qh
  if available>50:
   image=root/f'assets/objects/{self.icon}.webp';im=PILImage.open(image);scale=min((CW-40)/im.width,available/im.height);iw,ih=im.width*scale,im.height*scale;c.drawImage(str(image),x+(CW-iw)/2,y+42+qh+(available-ih)/2,iw,ih,mask='auto')
  c.restoreState()
class HeroSheet(Flowable):
 """Una página con retrato completo, biografía íntegra y cuatro tarjetas legibles."""
 def __init__(self,a):super().__init__();self.a=a;self.width=PW;self.height=FH-1
 def draw(self):
  c=self.canv;a=self.a;y=self.height
  c.setFillColor(RUBY);c.setFont('BodyBold',34);c.drawString(0,y-31,a['name']);c.setFont('BodyItalic',13);c.drawString(0,y-51,a['system']['shortDescription']);y-=69
  bio=blocks(a['system']['biography'],'hero',True)
  # La ilustración tiene su propia columna y mantiene cuerpo, equipo y silueta completos.
  bioWidth=PW-169;bh=sum(f.wrap(bioWidth,1000)[1]+f.getSpaceAfter() for f in bio)
  topHeight=max(265,bh)
  im=PILImage.open(artpath(a['name'].lower()));iw,ih=im.size;sc=min(148/iw,(topHeight-10)/ih)
  c.drawImage(jpeg(artpath(a['name'].lower())),(149-iw*sc)/2,y-ih*sc-3,iw*sc,ih*sc,mask='auto')
  yy=y
  for f in bio:
   _,hh=f.wrap(bioWidth,1000);f.drawOn(c,169,yy-hh);yy-=hh+f.getSpaceAfter()
  y-=topHeight+9
  themes=[i for i in a['items'] if i['type']=='themebook'];cells=[]
  for it in themes:
   s=it['system'];cell=[p(esc(it['name']),'themehead'),p('<b>Motivación.</b> '+esc(s['quest']),'theme')]
   cell += [p('• '+esc(t['name']),'theme') for t in s.get('powertags',[]) if not t.get('planned')]
   cell += [p('<b>Debilidad.</b> '+esc(' · '.join(t['name'] for t in s.get('weaknesstags',[]))),'theme')]
   cells.append(cell)
  table=Table([[cells[0],cells[1]],[cells[2],cells[3]]],colWidths=[PW/2,PW/2]);table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,-1),HexColor('#ece2d0')),('BOX',(0,0),(-1,-1),.55,GOLD),('INNERGRID',(0,0),(-1,-1),.4,GOLD),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),6)]));_,hh=table.wrap(PW,1000);table.drawOn(c,0,y-hh);y-=hh+8
  equipment=' · '.join(t['name'] for i in a['items'] if i['type']=='backpack' for t in i['system'].get('items',[]))
  rel=a['system'].get('fellowships',[{}])[0]
  foot=p('<b>Equipo.</b> '+esc(equipment)+'<br/><b>Relación con '+esc(rel.get('companion',''))+'.</b> '+esc(rel.get('relationshipTag','')),'small');_,hh=foot.wrap(PW,1000);foot.drawOn(c,0,y-hh);y-=hh
  if y<0:raise ValueError(f'Ficha desborda: {a["name"]}, {y:.1f} puntos')
class DocumentCard(Flowable):
 def __init__(self,h):
  super().__init__();self.h=h;self.width=CW;self.parts=[p(esc(h['title']),'themehead')]+blocks(h['body'],'handout');self.height=sum(f.wrap(CW-26,1000)[1]+f.getSpaceAfter() for f in self.parts)+30
 def draw(self):
  c=self.canv;c.setFillColor(HexColor('#eee4d0'));c.setStrokeColor(GOLD);c.setLineWidth(.6);c.rect(0,0,CW,self.height,fill=1,stroke=1);y=self.height-14
  for f in self.parts:
   _,hh=f.wrap(CW-26,1000);f.drawOn(c,13,y-hh);y-=hh+f.getSpaceAfter()
class MapPanel(Flowable):
 """Mapa grabado: la misma imagen maestra que alimenta las escenas de Foundry."""
 def __init__(self,kind,w=PW,h=370):super().__init__();self.kind=kind;self.width=w;self.height=h
 def draw(self):
  path=artpath('mapa-'+self.kind+'-piedra');self.canv.drawImage(jpeg(path),0,0,self.width,self.height)
class Book(BaseDocTemplate):
 def __init__(self,path,kind,**kw):
  super().__init__(str(path),pagesize=(W,H),leftMargin=M,rightMargin=M,topMargin=50,bottomMargin=50,pageCompression=1,**kw);self.kind=kind;self.platepages=[]
  def frame(x,w,id):return Frame(x,48,w,FH,id=id,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
  self.addPageTemplates([PageTemplate('art',[frame(M,PW,'art')]),PageTemplate('single',[frame(M,PW,'single')],onPage=self.page),PageTemplate('columns',[frame(M,CW,'left'),frame(M+CW+22,CW,'right')],onPage=self.page)])
 def page(self,c,d):
  c.setFillColor(PAPER);c.rect(0,0,W,H,fill=1,stroke=0);c.setStrokeColor(GOLD);c.setLineWidth(.45);c.line(M,H-34,W-M,H-34);c.line(M,34,W-M,34)
  c.setFont('BodyBold',8);c.setFillColor(RUBY);c.drawString(M,H-26,'EL TRONO DE LA SED');c.setFont('Body',8);c.drawRightString(W-M,H-26,self.kind.upper());c.setFillColor(HexColor('#6b5c4b'));c.drawString(M,23,'MANUEL ROMERA · PROYECTO MR');c.drawRightString(W-M,23,str(d.page))
 def afterFlowable(self,f):
  if isinstance(f,Plate):self.platepages.append(self.page)
  title=getattr(f,'toc',None)
  if title:
   key='bookmark-'+str(self.page)+'-'+str(len(title));self.canv.bookmarkPage(key);self.canv.addOutlineEntry(title,key,0,False);self.notify('TOCEntry',(0,title,self.page,key))
def heading(t,toc=True):
 x=p(t,'h1');x.toc=t if toc else None;return x
def switch(template):return [NextPageTemplate(template),PageBreak()]
def plate(art,title,kicker,quote='',toc=None):return switch('art')+[Plate(art,title,kicker,quote,toc=toc)]+switch('columns')
def illustration(name,caption,width=CW):
 path=artpath(name);im=PILImage.open(path);height=width*im.height/im.width
 return [KeepTogether([Image(jpeg(path),width=width,height=height),p(caption,'caption')])]
def reference_image(art,title,text):
 image=Image(jpeg(artpath(art)),width=300,height=300*PILImage.open(artpath(art)).height/PILImage.open(artpath(art)).width)
 t=Table([[image,[p(title,'h2'),p(text,'small')]]],colWidths=[313,PW-313]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0)]));return [Spacer(1,14),t]
def figure(f):
 data=[[p(esc(c),'small') for c in f['headers']]]+[[p(esc(c),'small') for c in row] for row in f['rows']]
 widths=([.18,.4,.42] if len(f['headers'])==3 else [.19,.27,.27,.27]);t=Table(data,colWidths=[PW*v for v in widths],repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#d8c7a5')),('ROWBACKGROUNDS',(0,1),(-1,-1),[PAPER,HexColor('#ece3d2')]),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,0),.7,GOLD),('INNERGRID',(0,1),(-1,-1),.3,HexColor('#cdbb98')),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
 return [p(esc(f['title']),'h2'),t,p(esc(f.get('note','')),'caption')]
secrets=json.loads((root/'content/personal-secrets.json').read_text());story=json.loads((root/'content/narrative.json').read_text());actors=json.loads((root/'content/actors.json').read_text());heroes=[a for a in actors if a['type']=='litm-character']
manual=[Plate('scene-neb-sekhem','EL TRONO<br/>DE LA SED','Manual del Narrador · Legend in the Mist',cover=True)]+switch('single')
manual += [p('Una ciudad que empieza a olvidar','h1'),p('Tres sesiones de horror gótico para cuatro o cinco protagonistas. Un funeral imposible conduce a una corte que se alimenta de nombres. Seis personas siguen vivas; un séptimo nombre puede abrir una prisión milenaria. La decisión final pertenece a los héroes.'),p('En estas páginas','h2')]
toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc',fontName='Body',fontSize=11.5,leading=14,spaceBefore=3,textColor=INK)];manual += [toc,Spacer(1,12),p('Cómo usar el libro','h2'),p('El texto sobre fondo de tinta es una voz para leer en mesa; el resto es información del Narrador. Las escenas admiten rutas alternativas y las pistas esenciales no dependen de una sola tirada. Los planos orientan: no fijan distancias. Las fichas usan los temas, etiquetas y desafíos nativos del sistema oficial. Este libro acompaña a su reglamento.')]+switch('columns')
inline={('sesion1',2):('scene-casa-panehsy','El archivo conserva las líneas que sus dueños no se atreven a leer.'),('sesion1',4):('scene-casa-nefru','Una segunda taza basta para que una ausencia se vuelva visible.'),('sesion1',7):('scene-pozo','Seis marcas usadas; una séptima ranura todavía limpia.'),('sesion2',0):('scene-entrada-palacio','La entrada ofrece hospitalidad antes de exigir obediencia.'),('sesion2',2):('banquete','Siete lugares preparados para una cena que todavía no ha terminado.'),('sesion2',8):('scene-galeria-rostros','El borrado deja huellas que se pueden escuchar, tocar y reconstruir.'),('sesion2',9):('scene-dormitorio-victimas','Las seis víctimas respiran. Sus nombres siguen cautivos.'),('sesion3',3):('pesaje','El cofre y la balanza son problemas distintos: ninguno exige una única solución.'),('finales',0):('scene-amanecer','Lo que vuelve a Muhar depende de los nombres que hayan sido sostenidos.')}
plates={'sesion1':('lamina-funeral','El funeral imposible','SESIÓN I · MUHAR','«No porque los muertos tengan sed. Porque los vivos olvidan beber.»'),'sesion2':('lamina-procesion','La corte bajo la arena','SESIÓN II · EL BANQUETE','La invitación promete un lugar. Nadie ha dicho qué habrá que dejar en él.'),'sesion3':('lamina-khety','El peso de un nombre','SESIÓN III · LA CÁMARA DEL PESAJE','Hay promesas que aprietan más que una cadena.'),'pnj':('lamina-merit','Una negativa completa','VOCES DE LA CORTE','Recordar a Merit también significa recordar que dijo no.'),'victimas':('lamina-nombres','Seis vidas, siete vasijas','LOS NOMBRES CAUTIVOS','Una ausencia no es una persona. Una vasija tampoco.')}
for idx,ch in enumerate(story['chapters'],1):
 if ch['id'] in plates:manual += plate(*plates[ch['id']])
 manual += [CondPageBreak(160),heading(f'{idx:02d} · '+ch['title'])]
 for i,s in enumerate(ch['sections']):
  manual += [p(s['title'],'h2')]
  # Retratos de apoyo pequeños; el texto continúa sin saltos impuestos por cada voz.
  npc=next((n.lower() for n in ['Merit','Khety','Tia','Panehsy','Nefru','Serekh'] if s['title'].startswith(n+' ')),None) if ch['id']=='pnj' else None
  if npc:
   parts=blocks(s['body']);first=parts.pop(0);t=Table([[Image(str(root/f'assets/npc/{npc}-portrait.webp'),width=92,height=92),first]],colWidths=[102,CW-102]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),5)]));manual += [t]+parts
  else:manual += blocks(s['body'])
  if (ch['id'],i) in inline:manual += illustration(*inline[ch['id'],i])
# Los finales de parte aprovechan la columna libre para una referencia ilustrada.
 if ch['id']=='verdad':manual += [Coda('vasija-septima','Dos sellos,<br/>dos decisiones','<b>Merit.</b> Su sello retiene al vampiro mientras sobreviva un testimonio auténtico de su identidad y de su negativa: una copia conservada o un testigo que la comprenda.<br/><br/><b>Los nombres.</b> La segunda prisión solo se abre cuando el séptimo nombre robado llega en su vasija al altar.<br/><br/>Neb-Sekhem solo sale del palacio si ambos sellos han caído. Sigue dentro de Ravenloft.','Rescatar los cuerpos y devolver los nombres son tareas distintas.')]
 if ch['id']=='finales':manual += plate('scene-coronacion','Si la sed recibe una corona','DESENLACE POSIBLE · SOLO NARRADOR','La libertad del vampiro no tiene por qué ser el final de vuestra historia.')
 if ch['id']=='sesion3':manual += [Coda('corazon','Antes de cerrar<br/>la cámara','Comprueba el corazón, las seis vasijas, el testimonio de Merit y la custodia elegida.<br/><br/>Destruir el corazón termina con el vampiro. No libera por sí solo los nombres.<br/><br/>Una victoria incompleta deja tareas concretas: rehacer registros, acompañar a las víctimas y decidir quién conserva las pruebas.','Da una escena a cada víctima y una pregunta a cada héroe.')]
 if ch['id']=='pnj':manual += [Coda('pluma','Una voz<br/>no es una solución','Cada voz desea algo, oculta algo y puede cambiar ante una prueba.<br/><br/>Merit conserva su capacidad de negarse. Khety necesita afrontar su responsabilidad. La autoridad de Serekh no lo vuelve infalible.<br/><br/>Ningún aliado debe resolver por los protagonistas lo que ellos todavía pueden decidir.','Escucha lo que una persona pide. Muestra lo que hará si nadie responde.')]
# Referencia reunida: dos tablas por página, sin portadillas vacías.
manual += switch('single')+[heading('Herramientas para dirigir'),p('Consulta estas relaciones de un vistazo cuando la mesa cambie el orden de los acontecimientos. La matriz ofrece rutas alternativas; los sellos conservan causas concretas y visibles.','small')]
for f in story['figures'][:2]:manual += figure(f)
manual += reference_image('scene-procesion','Seguir una huella','Una pista razonable se obtiene sin una tirada obligatoria. Las rutas alternativas permiten comprobarla, entender su coste o actuar antes que los adversarios. Si los héroes cambian el orden de las visitas, conserva las causas de los hechos y deja que la historia se mueva con ellos.')
manual += switch('single')
for f in story['figures'][2:]:manual += figure(f)
manual += [p('Cuatro hechos que conviene tener a la vista','h2'),p('Dónde está la séptima vasija · quién protege a Henut · qué testimonios de Merit sobreviven · quién controla el corazón. Cambia cada hecho solo cuando algo ocurra en la ficción y deja una señal que los héroes puedan percibir.','quote')]
manual += reference_image('merit-eco','Sostener un testimonio','El nombre de Merit importa junto con su voluntad. Aprender lo ocurrido puede fortalecer su sello; no lo rompe por sí solo. Quien escuche su historia puede conservar una copia, convertirse en testigo y elegir cómo responder ante la corte.')
manual += switch('single')+[heading('Planos de la aventura'),p('Muhar · Rutas de investigación','h2'),MapPanel('muhar',h=300),p('1 · Funeral · 2 · Archivo de Panehsy · 3 · Taller de Tia · 4 · Casa de Nefru · 5 · Camino al pozo','small'),p('Grabado de orientación sobre piedra. Un camino no obliga a visitar los lugares en este orden; combina visitas si necesitas acelerar la sesión.','caption'),p('El pozo · Seis marcas y un hueco limpio','h2')]
well=MapPanel('pozo',w=285,h=285);note=[p('La señal que falta','h2'),p('Las seis marcas usadas corresponden a los nombres ya robados. La séptima permanece limpia. El descenso conduce al Laberinto; el plano no revela una puerta secreta ni sustituye la investigación.'),p('Norte orientativo. Sin escala métrica. Los peligros aparecen por acciones visibles y decisiones de los personajes.','small')];t=Table([[well,note]],colWidths=[290,PW-290]);t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0)]));manual += [t]
manual += switch('single')+[p('La Corte de las Siete Lenguas','h1'),MapPanel('corte',h=430),p('Grabado de orientación · los huecos en los muros son accesos · sin escala métrica','caption')]
roomnotes=[('1 · Vestíbulo','Protocolo, servicio y primera elección.'),('2 · Banquete','Hospitalidad, tentaciones y lugares vacíos.'),('3 · Galería','Rostros borrados, huellas que persisten.'),('4 · Dormitorio','Seis personas vivas que pueden ser rescatadas.'),('5 · Vasijas','La custodia de los nombres robados.'),('6 · Inscripción','El testimonio y la negativa de Merit.'),('7 · Pesaje','El corazón y la decisión final.')]
for i in range(0,len(roomnotes),2):
 cells=[p('<b>'+esc(n)+'.</b> '+esc(t),'small') for n,t in roomnotes[i:i+2]];cells+=['']*(2-len(cells));manual += [Table([cells],colWidths=[PW/2,PW/2],style=[('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),8)])]
manual += [p('La llave de servicio abre una ruta hacia la cámara; no abre por sí sola el cofre. Los héroes pueden llegar por otra vía y todavía deberán decidir cómo afrontar su contenido.','quote')]
# Las cinco fichas son idénticas en ambos cuadernos; los secretos quedan en un registro aparte.
for i,a in enumerate(heroes):
 manual += switch('single')
 if i==0:
  marker=Spacer(1,0);marker.toc='Los cinco protagonistas';manual.append(marker)
 manual += [HeroSheet(a)]
manual += plate('lamina-corazon','El corazón fuera del cuerpo','LA PRISIÓN DEL REY','Una promesa puede retener a un monstruo. Un corazón puede terminar con él.')
manual += [heading('Secretos de los protagonistas'),p('Entrégalos individualmente. Cada participante decide cuándo compartir su secreto; las voces de la corte no lo conocen sin una causa establecida en la ficción.')]
for a in heroes:manual += [p(a['name'],'h2'),p(secrets[a['name']],'quote')]
manual += [CondPageBreak(170),heading('Desafíos y amenazas'),p('Un límite expresa una forma de superar la oposición, no puntos de golpe. Usa el estado que corresponda a la vía elegida. Cuando la ficción resuelve el problema, no añadas una tirada.')]
for a in actors:
 s=a['system']
 if a['type']!='litm-npc' or (not s.get('limits') and not s.get('threatsAndConsequences')):continue
 manual += [CondPageBreak(100),Rule(),p(a['name'],'h2')]
 if s.get('shortDescription'):manual += blocks('<p>'+s['shortDescription']+'</p>')
 for lim in s.get('limits',[]):manual += [p('<b>'+esc(lim['name'])+' '+esc(lim['value'])+'.</b> '+esc(lim.get('consequence','')))]
 for aspect in s.get('mightyAspects',[]):manual += [p('<b>Might.</b> '+esc(aspect.get('level',''))+' · '+esc(aspect.get('aspect','')))]
 for f in s.get('specialFeatures',[]):manual += blocks('<p><b>'+f['name']+'.</b> '+f['description']+'</p>')
 for t in s.get('threatsAndConsequences',[]):
  manual += blocks('<p><b>'+t['name']+'.</b> '+t.get('description','')+'</p>')
  for x in t.get('list',[]):manual += blocks('<p>• '+x+'</p>')
manual += [CondPageBreak(180),heading('Documentos para descubrir'),p('Recorta y entrega solo la pieza encontrada. Estos documentos pertenecen al manual privado. El cuaderno inicial no contiene estas revelaciones. Las condiciones de entrega figuran en los diarios del módulo.','small')]
for h in story['handouts']:
 if h.get('reveal')!='initial':manual += [Spacer(1,10),DocumentCard(h)]
manual += switch('columns')+[heading('Foundry, autoría y edición'),p('Instala mist-engine-fvtt 14.5.4 en Foundry v13. Descomprime el ZIP del módulo en Data/modules y actívalo en tu mundo. Acepta la importación en un mundo vacío, o abre Configuración → MR · El Trono de la Sed → Libro de los Muertos → Importar la aventura. Asigna un propietario a cada héroe; la compañía ya está vinculada.'),p('Alt+B abre el Libro de los Muertos y Alt+M, el Libro de los Recuerdos. El Narrador muestra cada documento cuando se descubre. Las fichas oficiales administran estados y etiquetas. La reimportación añade documentos ausentes y conserva los existentes.'),p('Antes de cambiar de navegador u ordenador, descarga una copia privada de campaña desde la Guía del Narrador. Su clave de cifrado permanece en el navegador. Conserva la copia como material privado: contiene tus notas legibles.'),p('Neb-Sekhem conserva la identidad de la referencia aportada. Toda la colección ha sido redibujada con tinta y planos de color. Publicación de Manuel Romera para Foundry VTT.','small'),p('La barra superior del Narrador reúne Leer escena, Mostrar a todos, Música, Modo lectura y Parar audio. Su menú permite ajustar el volumen y traer protagonistas. Cada escena tiene un diario privado con la lectura, el reparto, los objetos y los efectos apropiados. Mostrar a todos activa la escena y su música instrumental en bucle; el modo lectura reduce el fondo. Los efectos y ambientes se disparan por separado. La parada de audio afecta solo a este módulo.'),p('En una actualización, reimporta la aventura para añadir los nuevos diarios y listas de reproducción. Los enlaces de dirección se completan en las escenas originales sin reemplazar tus imágenes, textos ni progreso. Los créditos de música están dentro del módulo y en AUDIO-CREDITS.md.'),p('Las láminas y las dos escenas de Neb-Sekhem también están disponibles en la carpeta Escenas ilustradas del módulo. Son imágenes narrativas verticales para mostrar a la mesa; los tres planos siguen ofreciendo la orientación de juego.','small')]
manual += [p('Banda sonora instrumental','h2'),p('Música de Kevin MacLeod (incompetech.com), Creative Commons Attribution 4.0. Edición: recorte, bucle y normalización.','small')]
for d in json.loads((root/'content/audio.json').read_text()):
 if d['kind']=='music':manual += [p(esc(d['name'])+' · «'+esc(d['title'])+'» — Kevin MacLeod.','small')]
for para in (root/'NOTICE.md').read_text().split('\n\n'):
 if para.startswith('#'):manual.append(p(esc(para.lstrip('# ').strip()),'h2'))
 elif not para.startswith('Fuentes consultadas:'):manual.append(p(esc(para).replace('\n','<br/>'),'small'))
manual += switch('art')+[Plate('scene-amanecer','Nadie debería ser<br/>una ausencia','EL TRONO DE LA SED',story['closingQuestion'])]
book=Book(out/'El-Trono-de-la-Sed-Manual.pdf','Manual del Narrador',title='El Trono de la Sed · Manual del Narrador',author='Manuel Romera');book.multiBuild(manual)
import sys
if '--manual-only' in sys.argv:
 print('Manual revisado:',out/'El-Trono-de-la-Sed-Manual.pdf');sys.exit(0)
players=[Plate('lamina-funeral','EL TRONO<br/>DE LA SED','Cuaderno de protagonistas · Legend in the Mist',cover=True)]+switch('columns')
for ch in story['chapters']:
 if ch['audience']=='players':
  players += [heading(ch['title'])]
  for s in ch['sections']:players += [p(s['title'],'h2')]+blocks(s['body'])
players += illustration('scene-muhar','Muhar: el hogar que elegís recordar.')
for a in heroes:players += switch('single')+[HeroSheet(a)]
players += switch('columns')+[heading('El compromiso compartido')]
for h in story['handouts']:
 if h.get('reveal')=='initial':players += [p(h['title'],'h2')]+blocks(h['body'])
players += [p('Recuerdos propios','h2'),p('Anota un nombre, una relación, un recuerdo y un objeto que te ayude a conservarlo. Decide junto al grupo qué detalles puede conocer cada protagonista. En Foundry, abre el Libro de los Recuerdos con Alt+M. Los documentos del misterio se muestran durante la partida.'),p('Un espacio para vuestra promesa','h2'),p('Nombre: __________________________________<br/><br/>Detalle que recordaré: _________________________<br/><br/>Quien puede atestiguarlo: ______________________<br/><br/>Objeto que conservo: _________________________<br/><br/><br/>_________________________________________<br/><br/>_________________________________________<br/><br/>_________________________________________<br/><br/>_________________________________________<br/><br/>_________________________________________<br/><br/>_________________________________________<br/><br/>_________________________________________<br/><br/>_________________________________________<br/><br/>_________________________________________<br/><br/>_________________________________________<br/><br/>_________________________________________<br/><br/>_________________________________________','small')]
playerbook=Book(out/'El-Trono-de-la-Sed-Material-de-Juego.pdf','Cuaderno de protagonistas',title='El Trono de la Sed · Cuaderno de protagonistas',author='Manuel Romera');playerbook.multiBuild(players)
print('PDF revisados:',out)
