"""Edición A4 reproducible desde narrativa y datos nativos; no copia el manual del sistema."""
from pathlib import Path
import json,re,html
from reportlab.platypus import BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,PageBreak,NextPageTemplate,Image,KeepTogether,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus.tableofcontents import TableOfContents
root=Path(__file__).resolve().parents[1];out=root/'output/pdf';out.mkdir(parents=True,exist_ok=True)
for name,f in [('Body','EBGaramond-Regular.ttf'),('BodyBold','EBGaramond-Bold.ttf'),('BodyItalic','EBGaramond-Italic.ttf')]:
 pdfmetrics.registerFont(TTFont(name,str(root/'editorial/fonts'/f)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='BodyItalic',boldItalic='BodyBold')
styles={
 'body':ParagraphStyle('body',fontName='Body',fontSize=11.2,leading=15.5,spaceAfter=9,textColor=HexColor('#27242a')),
 'h1':ParagraphStyle('h1',fontName='BodyBold',fontSize=26,leading=31,spaceAfter=20,textColor=HexColor('#5b2533')),
 'h2':ParagraphStyle('h2',fontName='BodyBold',fontSize=14,leading=18,spaceBefore=14,spaceAfter=10,textColor=HexColor('#5b2533'),keepWithNext=True),
 'quote':ParagraphStyle('quote',fontName='BodyItalic',fontSize=11,leading=16,spaceBefore=10,spaceAfter=14,leftIndent=10,rightIndent=8,borderColor=HexColor('#b7975b'),borderWidth=1,borderPadding=9,backColor=HexColor('#e6ddcb')),
 'small':ParagraphStyle('small',fontName='Body',fontSize=9.5,leading=13,spaceAfter=8),
 'title':ParagraphStyle('title',fontName='BodyBold',fontSize=36,leading=42,textColor=HexColor('#e3d5b8'),spaceAfter=26),
 'subtitle':ParagraphStyle('subtitle',fontName='Body',fontSize=15,leading=22,textColor=HexColor('#d9bd83'),spaceAfter=15)}
W,H=595.276,841.89
class Book(BaseDocTemplate):
 def __init__(self,path,**kw):
  super().__init__(str(path),pagesize=(W,H),leftMargin=44,rightMargin=44,topMargin=55,bottomMargin=48,**kw)
  self.addPageTemplates([PageTemplate(id='cover',frames=[Frame(45,80,W-90,H-140,id='cover',leftPadding=0,bottomPadding=0,rightPadding=0,topPadding=0)],onPage=self.cover),PageTemplate(id='single',frames=[Frame(44,48,W-88,H-105,id='single',leftPadding=0,bottomPadding=0,rightPadding=0,topPadding=0)],onPage=self.page),PageTemplate(id='columns',frames=[Frame(44,48,(W-108)/2,H-105,id='left',leftPadding=0,bottomPadding=0,rightPadding=0,topPadding=0),Frame((W+20)/2,48,(W-108)/2,H-105,id='right',leftPadding=0,bottomPadding=0,rightPadding=0,topPadding=0)],onPage=self.page),PageTemplate(id='handout',frames=[Frame(80,95,W-160,H-190,id='handout',leftPadding=0,bottomPadding=0,rightPadding=0,topPadding=0)],onPage=self.handout),PageTemplate(id='back',frames=[Frame(45,80,W-90,H-140,id='back',leftPadding=0,bottomPadding=0,rightPadding=0,topPadding=0)],onPage=self.back)])
 def cover(self,c,d):
  c.setFillColor(HexColor('#181b26'));c.rect(0,0,W,H,fill=1,stroke=0)
  p=root/'art/masters/pesaje.png'
  if p.exists(): c.drawImage(str(p),0,250,width=W,height=340,mask='auto')
  c.setStrokeColor(HexColor('#b7975b'));c.rect(25,25,W-50,H-50,fill=0,stroke=1)
 def page(self,c,d):
  c.setFillColor(HexColor('#f4efdf'));c.rect(0,0,W,H,fill=1,stroke=0)
  c.setFillColor(HexColor('#25232d'));c.rect(0,H-30,W,30,fill=1,stroke=0)
  c.setFont('Body',8);c.setFillColor(HexColor('#e4d4ae'));c.drawString(44,H-20,'MR · EL TRONO DE LA SED');c.drawRightString(W-44,H-20,'EDICIÓN LOCAL · 0.1.0')
  c.setStrokeColor(HexColor('#b7975b'));c.line(44,35,W-44,35)
  c.setFillColor(HexColor('#594f48'));c.drawString(44,22,'Manuel Romera · Legend in the Mist');c.drawRightString(W-44,22,str(d.page))
 def back(self,c,d):
  c.setFillColor(HexColor('#181b26'));c.rect(0,0,W,H,fill=1,stroke=0)
  art=root/'art/masters/merit-eco.png'
  if art.exists():c.drawImage(str(art),0,270,width=W,height=335,mask='auto')
  c.setStrokeColor(HexColor('#b7975b'));c.rect(25,25,W-50,H-50,fill=0,stroke=1)
 def handout(self,c,d):
  Book.page(self,c,d);c.setStrokeColor(HexColor('#b7975b'));c.setLineWidth(1.1);c.rect(45,62,W-90,H-124,stroke=1,fill=0)
  for i in range(7):c.circle(W/2+(i-3)*16,H-72,3,stroke=1,fill=0)
 def afterFlowable(self,f):
  if isinstance(f,Paragraph) and f.style.name=='h1':
   text=f.getPlainText();key='p'+str(self.page)+'-'+str(len(text));self.canv.bookmarkPage(key);self.canv.addOutlineEntry(text,key,0,False);self.notify('TOCEntry',(0,text,self.page,key))
def p(text,style='body'):return Paragraph(re.sub(r'<br\s*/?>','<br/>',text,flags=re.I),styles[style])
def blocks(source):
 out=[]
 for tag,body in re.findall(r'<(p|blockquote|h3|ul|ol)\b[^>]*>(.*?)</\1>',source,re.S):
  if tag in ('ul','ol'):
   out.extend(p('• '+x) for x in re.findall(r'<li>(.*?)</li>',body,re.S))
  else:out.append(p(body,'quote' if tag=='blockquote' else 'h2' if tag=='h3' else 'body'))
 if not out:out=[p(re.sub('<[^>]+>','',source))]
 return out
secrets=json.loads((root/'content/personal-secrets.json').read_text())
story=json.loads((root/'content/narrative.json').read_text());actors=json.loads((root/'content/actors.json').read_text())
def opening(subtitle):
 return [Spacer(1,15),p('MR · EL TRONO<br/>DE LA SED','title'),p('LA CORTE DEL REY SIN NOMBRE','subtitle'),Spacer(1,370),p(subtitle,'subtitle'),p('Manuel Romera · Edición local de trabajo','subtitle'),NextPageTemplate('single'),PageBreak()]
manual=opening('Manual del Narrador · Horror gótico para Legend in the Mist')
manual += [p('Antes de abrir la corte','h1'),p('Esta edición local utiliza Har’Akir y Ravenloft como marco de una aventura original para cuatro o cinco personas. No es un producto oficial ni una edición autorizada para distribución. El texto y la implementación se están sometiendo a pruebas. El arte definitivo de Neb-Sekhem necesita la imagen original de referencia.'),p('Cómo leer','h2'),p('Los recuadros recogen textos que puedes leer en voz alta. El resto describe hechos, decisiones y consecuencias para el Narrador. Las reglas se resuelven con las fichas del sistema oficial: este libro no sustituye su reglamento.'),p('Índice','h1')]
toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc',fontName='Body',fontSize=10,leading=15,spaceBefore=5)];manual += [toc]
chapter_art={'umbral':'scene-muhar','direccion':'scene-taller-tia','verdad':'scene-sala-vasijas','sesion1':'funeral','sesion2':'banquete','sesion3':'pesaje','pnj':'scene-casa-panehsy','victimas':'scene-dormitorio-victimas','finales':'scene-amanecer','consulta':'scene-pozo'}
for chapter in story['chapters']:
 manual += [NextPageTemplate('single'),PageBreak(),p(chapter['title'],'h1')]
 # Apertura ilustrada seguida de lectura en dos columnas; la misma obra conserva su función de localización.
 picture=root/f'art/masters/{chapter_art[chapter["id"]]}.png'
 if picture.exists():manual += [Image(str(picture),width=W-88,height=(W-88)*.563),Spacer(1,14)]
 manual += [NextPageTemplate('columns')]
 for section in chapter['sections']:
  manual += [p(section['title'],'h2')]
  npc=next((name.lower() for name in ['Merit','Khety','Tia','Panehsy','Nefru','Serekh'] if section['title'].startswith(name+' ')),None) if chapter['id']=='pnj' else None
  if npc:
   picture=root/f'art/masters/npc-{npc}.png'
   if picture.exists():manual += [Image(str(picture),width=205,height=205,hAlign='LEFT'),Spacer(1,10)]
  manual += blocks(section['body'])
for fig in story.get('figures',[]):
 manual += [NextPageTemplate('single'),PageBreak(),p(fig['title'],'h1')]
 data=[[p(html.escape(c),'small') for c in fig['headers']]]+[[p(html.escape(c),'small') for c in row] for row in fig['rows']]
 table=Table(data,colWidths=[(W-88)/len(fig['headers'])]*len(fig['headers']),repeatRows=1,hAlign='LEFT')
 table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor('#ded0b2')),('ROWBACKGROUNDS',(0,1),(-1,-1),[HexColor('#f4efdf'),HexColor('#eae2cf')]),('VALIGN',(0,0),(-1,-1),'TOP'),('BOX',(0,0),(-1,-1),.6,HexColor('#a78a50')),('INNERGRID',(0,0),(-1,-1),.3,HexColor('#c9b890')),('TOPPADDING',(0,0),(-1,-1),12),('BOTTOMPADDING',(0,0),(-1,-1),12)]))
 manual += [table,Spacer(1,15),p(fig.get('note',''),'small')]
manual += [NextPageTemplate('single'),PageBreak(),p('Personajes preparados','h1'),p('Cada protagonista dispone de cuatro temas iniciales, una relación mecánica y una mochila nativa. Los vínculos adicionales desarrollan la interpretación; solo las etiquetas pertinentes se seleccionan para una acción.')]
for a in actors:
 if a['type']!='litm-character':continue
 manual += [NextPageTemplate('single'),PageBreak(),p(a['name'],'h1'),p(a['system']['shortDescription'],'h2')]
 portrait=root/f'assets/characters/{a["name"].lower()}-portrait.webp'
 if portrait.exists():manual += [Image(str(portrait),width=165,height=165,hAlign='LEFT'),Spacer(1,12)]
 manual += [p('Secreto personal · entrégalo en privado','h2'),p(secrets[a['name']],'quote'),NextPageTemplate('columns')]+blocks(a['system']['biography'])
 for it in a.get('items',[]):
  if it['type']=='themebook':
   s=it['system'];manual += [p(it['name'],'h2'),p('<b>Motivación:</b> '+html.escape(s['quest'])),p('<b>Poder:</b> '+html.escape(' · '.join(x['name'] for x in s.get('powertags',[]) if not x.get('planned')))),p('<b>Debilidad:</b> '+html.escape(' · '.join(x['name'] for x in s.get('weaknesstags',[]))))]
manual += [NextPageTemplate('single'),PageBreak(),p('Desafíos y amenazas nativos','h1'),p('Los límites describen formas concretas de superar una oposición. No son puntos de golpe. Aplica solo un estado que corresponda a la situación y a la vía de resolución elegida. La ficción puede hacer innecesaria una tirada.')]
for a in actors:
 if a['type']!='litm-npc':continue
 s=a['system']
 if not s.get('limits') and not s.get('threatsAndConsequences'):continue
 card=[p(a['name'],'h2')]
 if s.get('shortDescription'):card += blocks('<p>'+s['shortDescription']+'</p>')
 for lim in s.get('limits',[]):card += [p('<b>Límite: '+html.escape(lim['name'])+' '+html.escape(str(lim['value']))+'</b> - '+html.escape(lim.get('consequence','')))]
 for aspect in s.get('mightyAspects',[]):card += [p('<b>Might: </b>'+html.escape(aspect.get('level',''))+' · '+html.escape(aspect.get('aspect','')))]
 for feature in s.get('specialFeatures',[]):card += [p(feature['name'],'h2')]+blocks('<p>'+feature['description']+'</p>')
 for threat in s.get('threatsAndConsequences',[]):
  card += [p(threat['name'],'h2')]+blocks('<p>'+threat.get('description','')+'</p>')
  for consequence in threat.get('list',[]):card += blocks('<p>'+consequence+'</p>')
 manual += [KeepTogether(card),Spacer(1,24)]

manual += [NextPageTemplate('single'),PageBreak(),p('Documentos para descubrir','h1'),p('Estas hojas forman parte del manual privado. Imprime o muestra únicamente el documento que corresponda al descubrimiento realizado. Las condiciones de entrega permanecen en los diarios privados de Foundry. El cuaderno inicial de jugadores no contiene estas revelaciones.')]
for h in story.get('handouts',[]):
 if h.get('reveal')!='initial':
  manual += [NextPageTemplate('handout'),PageBreak(),p(h['title'],'h1'),Spacer(1,24)]
  hs=ParagraphStyle('handout-text',parent=styles['body'],fontSize=14,leading=22,spaceAfter=16)
  manual += [Paragraph(b.text,hs) if isinstance(b,Paragraph) else b for b in blocks(h['body'])]
  icon={'invitacion':'invitacion','pluma-merit':'pluma','fragmento-cancion':'arpa','inscripcion-merit':'pluma','recibo':'escarabajo'}.get(h['id'])
  if icon:manual += [Spacer(1,20),Image(str(root/f'assets/objects/{icon}.webp'),width=170,height=170)]
manual += [NextPageTemplate('single'),PageBreak(),p('Foundry y créditos','h1'),p('Instala el sistema oficial mist-engine-fvtt 14.5.4 en Foundry v13. Descomprime mr-trono-de-la-sed.zip dentro de Data/modules. Activa el módulo en tu mundo. Acepta la importación ofrecida en un mundo vacío, o usa Configuración → MR · El Trono de la Sed → Libro de los Muertos → Importar la aventura. Asigna un propietario a cada héroe; la compañía ya está vinculada.'),p('Abre el Libro de los Muertos con Alt+B y el Libro de los Recuerdos con Alt+M. El Narrador muestra cada documento cuando se descubre. Los estados y las etiquetas se administran desde las fichas oficiales. La reimportación añade documentos ausentes y conserva los que ya existen. Las imágenes de ficha se asignan con las propiedades nativas del sistema.'),p('Antes de cambiar de navegador u ordenador, descarga una copia privada de campaña desde la Guía del Narrador. Las notas se guardan cifradas y su clave permanece en el navegador. Si no está disponible, el panel permite recuperar una copia sin reiniciar la aventura. Guarda ese fichero como material privado: contiene tus anotaciones legibles.'),p('Las pruebas y la evidencia técnica se conservan fuera del libro en docs. Esta edición permanece local y no tiene manifiesto remoto ni Release.') ]
for path in ['NOTICE.md']:
 if (root/path).exists():
  for para in (root/path).read_text().split('\n\n'):
   manual.append(p(html.escape(para).replace('\n','<br/>'),'small'))
manual += [NextPageTemplate('back'),PageBreak(),p('NADIE DEBERÍA SER<br/>UNA AUSENCIA','title'),Spacer(1,415),p(story['closingQuestion'],'subtitle')]
Book(out/'El-Trono-de-la-Sed-Manual.pdf',title='El Trono de la Sed · Manual',author='Manuel Romera').multiBuild(manual)
players=opening('Material de juego · Cuaderno de protagonistas')
for c in story['chapters']:
 if c['audience']=='players':
  players += [p(c['title'],'h1')]
  for s in c['sections']:players += [p(s['title'],'h2')]+blocks(s['body'])
for a in actors:
 if a['type']!='litm-character':continue
 slug=a['name'].lower();players += [PageBreak(),p(a['name'],'h1'),p(a['system']['shortDescription'],'h2')]
 portrait=root/f'assets/characters/{slug}-portrait.webp'
 if portrait.exists():players.append(Image(str(portrait),width=150,height=150,hAlign='LEFT'))
 players += blocks(a['system']['biography'])
 for it in a.get('items',[]):
  s=it['system']
  if it['type']=='themebook':players += [p(it['name'],'h2'),p(html.escape(s['quest'])),p('<b>Poder:</b> '+html.escape(' · '.join(x['name'] for x in s.get('powertags',[]) if not x.get('planned')))),p('<b>Debilidad:</b> '+html.escape(' · '.join(x['name'] for x in s.get('weaknesstags',[]))))]
  elif it['type']=='backpack':players += [p('Equipo','h2'),p(html.escape(' · '.join(x['name'] for x in s.get('items',[]))))]
for h in story.get('handouts',[]):
 if h.get('reveal')=='initial':players += [PageBreak(),p(h['title'],'h1')]+blocks(h['body'])
players += [PageBreak(),p('Recuerdos propios','h1'),p('Anota un nombre, una relación, un recuerdo y un objeto que te ayude a conservarlo. Decide junto al grupo qué detalles puede conocer cada protagonista. En Foundry, abre el Libro de los Recuerdos desde la configuración del módulo o mediante Alt+M.'),p('No se incluyen aquí los documentos del misterio que deben descubrirse durante la partida. El Narrador puede mostrarlos individualmente desde Foundry en el momento indicado. Así puedes imprimir y leer este cuaderno sin adelantar revelaciones.')]
Book(out/'El-Trono-de-la-Sed-Material-de-Juego.pdf',title='El Trono de la Sed · Material de Juego',author='Manuel Romera').multiBuild(players)
print('PDF generados en',out)
