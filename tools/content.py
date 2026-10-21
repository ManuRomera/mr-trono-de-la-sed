"""Genera diarios, escenas, Adventure y manuscrito desde las fuentes estructuradas."""
from pathlib import Path
import json,hashlib,re,copy
root=Path(__file__).resolve().parents[1];mod='mr-trono-de-la-sed';prefix='modules/'+mod+'/'
def uid(value):return hashlib.sha256(value.encode()).hexdigest()[:16]
def read(p):return json.loads((root/p).read_text())
def flags(slug,audience='gm'):return {mod:{'source':mod,'slug':slug,'audience':audience}}
secrets=read('content/personal-secrets.json')
actors=read('content/actors.json');items=read('content/items.json');story=read('content/narrative.json');journals=[];md=[]
for a in actors:
 slug=a['name'].lower();a.setdefault('flags',{}).setdefault(mod,{}).update({'source':mod,'slug':slug})
 if a['type']=='litm-character':
  a['img']=prefix+f'assets/characters/{slug}-portrait.webp';a['system']['customBackground']=prefix+f'assets/characters/{slug}-sheet.webp';a['system']['customFontColor']='#f2e6c9'
  a['prototypeToken']={'name':a['name'],'actorLink':True,'texture':{'src':prefix+f'assets/characters/{slug}-token.webp'},'width':3.6,'height':3.6,'lockRotation':True,'disposition':1}
  a['ownership']={'default':0}
  a['system']['notes']+='<h3>Tu secreto personal · compartir solo si tú decides</h3><p>'+secrets[a['name']]+'</p>'
  a['flags'][mod]['memories']={'trueName':a['name'],'bonds':'Completa tus vínculos con el grupo antes de empezar.','changes':'','entries':[]}
object_images={'Escarabajo funerario':'escarabajo','Corazón de Neb-Sekhem':'corazon','Pluma de Merit':'pluma','Vasija de Hori':'vasija-hori','Vasija de Paser':'vasija-paser','Vasija de Tamerit':'vasija-tamerit','Vasija de Kasa':'vasija-kasa','Vasija de Beset':'vasija-beset','Vasija de Dedi':'vasija-dedi','Séptima vasija':'vasija-septima','Arpa de Seneb':'arpa','Invitación al banquete':'invitacion','Cofre del corazón':'corazon','Canto del testigo':'arpa','Contrafirma de la negativa':'pluma','Lectura del nombre velado':'escarabajo','Bendición del umbral recordado':'escarabajo'}
for a in actors:
 creature={'Sombras de chacal':'sombra-chacal','Custodios de la corte':'custodio','Servidores sin nombre':'servidor'}.get(a['name'])
 if creature:
  a['img']=prefix+f'assets/objects/{creature}.webp'
  a['prototypeToken']={'name':a['name'],'actorLink':False,'texture':{'src':a['img']},'width':3.6,'height':3.6,'lockRotation':True}
for it in items:
 slug=object_images.get(it['name'])
 if slug:it['img']=prefix+f'assets/objects/{slug}.webp'
 it.setdefault('flags',{}).setdefault(mod,{}).update({'source':mod,'slug':it['name'].lower()})
for a in actors:
 npcslug={'Merit':'merit','Khety':'khety','Tia':'tia','Panehsy':'panehsy','Nefru':'nefru','Serekh':'serekh','Neb-Sekhem':'neb-sekhem','Hori':'hori','Paser':'paser','Tamerit':'tamerit','Kasa':'kasa','Beset':'beset','Dedi':'dedi','Henut':'henut','Borrados':'borrado','Plañideras':'planidera','Pesadores':'pesador'}.get(a['name'])
 if npcslug:
  a['img']=prefix+f'assets/npc/{npcslug}-portrait.webp'
  a['flags'][mod]['thumbnail']=prefix+f'assets/npc/{npcslug}-thumb.webp'
  a['prototypeToken']={'name':a['name'],'actorLink':True,'texture':{'src':prefix+f'assets/npc/{npcslug}-token.webp'},'width':3.6,'height':3.6,'lockRotation':True}
 if a['type']=='litm-fellowship-themecard':a['ownership']={'default':3}
for a in actors:
 if not a.get('img') or a['img'].startswith('icons/'):
  visual={'El funeral imposible':'scenes/funeral','La memoria de Muhar':'scenes/muhar','La invitación':'objects/invitacion','El banquete':'scenes/banquete','El Laberinto':'scenes/laberinto','El pesaje':'scenes/pesaje'}.get(a['name'],'objects/escarabajo')
  a['img']=prefix+'assets/'+visual+'.webp'
for c in story['chapters']:
 pages=[];md.append('# '+c['title'])
 for i,s in enumerate(c['sections']):
  body=s['body'];pages.append({'_id':uid('edition-1.1/'+c['id']+'/'+str(i)),'name':s['title'],'type':'text','sort':i*100000,'title':{'show':True,'level':1},'text':{'format':1,'content':body}})
  md.extend(['## '+s['title'],re.sub('<[^>]+>','',body),''])
 journals.append({'_id':uid('edition-1.1/journal/'+c['id']),'name':c['title'],'pages':pages,'ownership':{'default':2 if c['audience']=='players' else 0},'flags':{mod:{**flags(c['id'],c['audience'])[mod],'editorialEdition':'1.1.0'}}})
for h in story.get('handouts',[]):
 journals.append({'_id':uid('handout/'+h['id']),'name':'Ayuda · '+h['title'],'pages':[{'_id':uid('page/'+h['id']),'name':h['title'],'type':'text','text':{'format':1,'content':h['body']}}],'ownership':{'default':0},'flags':{mod:{**flags(h['id'],'players')[mod],'reveal':h.get('reveal','')}}})
for fig in story.get('figures',[]):
 import html
 body='<table><thead><tr>'+''.join('<th>'+html.escape(h)+'</th>' for h in fig['headers'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+html.escape(c)+'</td>' for c in row)+'</tr>' for row in fig['rows'])+'</tbody></table><p>'+html.escape(fig.get('note',''))+'</p>'
 journals.append({'_id':uid('figure/'+fig['id']),'name':fig['title'],'pages':[{'_id':uid('figure-page/'+fig['id']),'name':fig['title'],'type':'text','text':{'format':1,'content':body}}],'ownership':{'default':0},'flags':flags(fig['id'])})
mapdata=read('content/maps-wide.json')['corte'];scenes=[]
mapscene={'_id':uid('scene/corte'),'name':'La Corte · Plano de orientación','width':1920,'height':1080,'padding':0,'grid':{'type':0,'size':100,'distance':1,'units':'pasos'},'background':{'src':prefix+'assets/maps/corte.svg'},'tokenVision':False,'fog':{'exploration':False},'globalLight':True,'navigation':False,'ownership':{'default':0},'flags':flags('corte'),'walls':[{'_id':uid('wall/'+str(i)),'c':c,'move':20,'sight':20,'light':20,'sound':20,'door':0} for i,c in enumerate(mapdata['walls'])]}
# Notas privadas con la clave del plano; las ayudas no revelan localizaciones por defecto.
mapscene['notes']=[]
mapscene['tokens']=[]
scenes.append(mapscene)
for slug,name,w,h in [('muhar','Muhar · Plano de rutas',1920,1080),('pozo','Pozo · Plano de las siete ranuras',1920,1080)]:
 scenes.append({'_id':uid('map/'+slug),'name':name,'width':w,'height':h,'padding':0,'grid':{'type':0,'size':100},'background':{'src':prefix+'assets/maps/'+slug+'.svg'},'tokenVision':False,'fog':{'exploration':False},'navigation':False,'flags':flags('map-'+slug)})
scene_names={'funeral':'El funeral imposible','banquete':'El banquete','pesaje':'La Cámara del Pesaje','laberinto':'El Laberinto','muhar':'Muhar al anochecer','casa-panehsy':'Casa de Panehsy','taller-tia':'Taller de Tia','casa-nefru':'Casa de Nefru','camino-chacales':'El camino de los chacales','procesion':'La procesión funeraria','pozo':'El pozo de las siete ranuras','entrada-palacio':'El umbral de la corte','galeria-rostros':'La galería de los rostros borrados','dormitorio-victimas':'El dormitorio de las víctimas','sala-vasijas':'La sala de las vasijas','inscripcion-merit':'El testimonio de Merit','amanecer':'El último amanecer','merit-eco':'Merit · El eco que elige','neb-sekhem':'Neb-Sekhem · La invitación del rey','coronacion':'Coronación · El triunfo de la sed'}
# Versiones panorámicas de las láminas: solo entorno para colocar tokens.
scene_names.update({'lamina-funeral':'Lámina · El funeral imposible','lamina-procesion':'Lámina · El descenso a la corte','lamina-nombres':'Lámina · Los nombres cautivos','lamina-corazon':'Lámina · El corazón y la balanza','lamina-merit':'Lámina · La negativa de Merit','lamina-khety':'Lámina · La falsa promesa de Khety'})
for slug,name in scene_names.items():
 asset=f'assets/scenes/{slug}.webp'
 if (root/asset).exists():
  from PIL import Image
  im=Image.open(root/asset)
  scenes.append({'_id':uid('scene/'+slug),'name':name,'width':im.width,'height':im.height,'padding':0,'grid':{'type':0,'size':100},'background':{'src':prefix+asset},'tokenVision':False,'fog':{'exploration':False},'navigation':False,'flags':flags(slug)})
macro={'_id':uid('macro/libros'),'name':'MR · Abrir el Libro de los Muertos','type':'script','scope':'global','command':f"game.modules.get('{mod}').api[game.user.isGM ? 'openGMBook' : 'openMemories']();",'ownership':{'default':2},'flags':flags('abrir-libros')}
folder_specs=[('heroes','Protagonistas','Actor'),('voices','Voces de la corte','Actor'),('victims','Las seis víctimas','Actor'),('challenges','Desafíos','Actor'),('rites','Ritos y técnicas','Item'),('objects','Objetos y testimonios','Item'),('guide-1.1','Manual del Narrador · edición revisada','JournalEntry'),('handouts','Documentos por descubrir','JournalEntry'),('players','Cuaderno inicial','JournalEntry'),('cinematic','Escenas ilustradas','Scene'),('maps','Planos de orientación','Scene'),('tools','Herramientas','Macro')]
folders=[{'_id':uid('folder/'+slug),'name':name,'type':type,'sorting':'a','color':'#6d2939','flags':flags('folder-'+slug)} for slug,name,type in folder_specs]
folder_id=lambda slug:uid('folder/'+slug)
for a in actors:
 category='heroes' if a['type'] in ['litm-character','litm-fellowship-themecard'] else 'victims' if a['name'] in ['Hori','Paser','Tamerit','Kasa','Beset','Dedi'] else 'voices' if a['name'] in ['Neb-Sekhem','Merit','Khety','Tia','Panehsy','Nefru','Serekh','Henut'] else 'challenges'
 a['folder']=folder_id(category)
for it in items:it['folder']=folder_id('rites' if it['type']=='rote' else 'objects')
for j in journals:j['folder']=folder_id('handouts' if j['name'].startswith('Ayuda ·') else 'players' if j['flags'][mod]['audience']=='players' else 'guide-1.1')
for scene in scenes:scene['flags'][mod]['presentationEdition']='1.1.0';scene['folder']=folder_id('maps' if scene['flags'][mod]['slug'].startswith('map-') or scene['flags'][mod]['slug']=='corte' else 'cinematic')
macro['folder']=folder_id('tools')
import runpy
playlists=runpy.run_path(str(root/'tools/director-content.py'))['add_direction'](root,uid,flags,prefix,actors,items,story,journals,scenes,folders)
adv={'_id':uid('adventure/trono'),'name':'MR · El Trono de la Sed — La Corte del Rey sin Nombre','description':'<p>Aventura completa con dirección de escenas, lecturas enlazadas y audio instrumental. La importación añade documentos ausentes y conserva los existentes.</p>','actors':actors,'items':items,'journal':journals,'scenes':scenes,'macros':[macro],'folders':folders,'playlists':playlists,'tables':[],'cards':[],'flags':flags('aventura')}
(root/'_data').mkdir(exist_ok=True);(root/'_data/aventura.json').write_text(json.dumps([adv],ensure_ascii=False,indent=2));(root/'docs/manuscrito.md').write_text('\n\n'.join(md))
print(json.dumps({'actors':len(actors),'items':len(items),'journals':len(journals),'scenes':len(scenes),'words':len(' '.join(md).split())}))
