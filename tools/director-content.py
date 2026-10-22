"""Une lecturas, reparto, objetos y sonido a cada escena desde las fuentes comunes."""
import html,re,json

def add_direction(root,uid,flags,prefix,actors,items,story,journals,scenes,folders):
 mod='mr-trono-de-la-sed';presentations=json.loads((root/'content/presentations.json').read_text());audio=json.loads((root/'content/audio.json').read_text());directions=json.loads((root/'content/direction.json').read_text())
 playlists=[];soundids={}
 for kind,title in [('music','MR · Música de la corte'),('sfx','MR · Efectos y ambientes')]:
  sounds=[];pid=uid('playlist/'+kind)
  for d in audio:
   if d['kind']!=kind:continue
   sid=uid('sound/'+kind+'/'+d['slug']);soundids[kind+'/'+d['slug']]=sid
   sounds.append({'_id':sid,'name':d['name'],'path':prefix+d['path'],'volume':.3 if kind=='music' else .4,'repeat':d['repeat'],'fade':3500 if kind=='music' else 250,'playing':False,'flags':{mod:{'slug':d['slug'],'source':mod,'kind':kind,'motif':bool(d.get('motif'))}}})
  playlists.append({'_id':pid,'name':title,'mode':-1,'sounds':sounds,'playing':False,'ownership':{'default':0},'flags':{mod:{'source':mod,'slug':kind,'kind':kind}}})
 folder=uid('folder/scene-guides');folders.append({'_id':folder,'name':'Dirección de escenas','type':'JournalEntry','sorting':'a','color':'#713447','flags':flags('folder/scene-guides')})
 chapters={c['id']:c for c in story['chapters']};people={a['name']:a for a in actors};objects={a['name']:a for a in items};by_slug={d['slug']:d for d in directions}
 def action(verb,arg,label):return '@Trono['+verb+'|'+arg+']{'+label+'}'
 for scene in scenes:
  slug=scene['flags'][mod]['slug'];d=by_slug[slug];section=chapters[d['chapter']]['sections'][d['section']];jid=uid('direction/'+slug);pageid=uid('direction-page/'+slug)
  reading=re.findall(r'<blockquote>(.*?)</blockquote>',section['body'],re.S)
  if not reading:raise ValueError('Escena sin lectura: '+slug)
  cast=[people[n] for n in d['actors']];props=[objects[n] for n in d['items']];sfx=d['effects']
  controls=' '.join([action('activate',slug,'Mostrar escena a todos'),action('music',slug,'Música de escena'),action('quiet',slug,'Bajar/restaurar fondo'),action('stop',slug,'Parar audio del módulo'),action('heroes',slug,'Traer protagonistas')])
  body='<section class="mr-scene-guide"><p class="mr-guide-kicker">DIRECCIÓN · SOLO NARRADOR</p><div class="mr-director-actions">'+controls+'</div><h2>Lee a los jugadores</h2>'+''.join('<blockquote>'+t+'</blockquote>' for t in reading)
  body+='<h2>Reparto en esta escena</h2><p>Abre las fichas o coloca figuras completas cuando la ficción lo justifique.</p><ul>'
  for a in cast:
   ak=a['flags'][mod]['slug'];body+='<li>'+action('actor',ak,a['name'])+' · '+action('token',slug+'~'+ak,'Colocar figura')+'</li>'
  body+='</ul><p>'+action('heroes',slug,'Colocar los cinco protagonistas')+'</p>'
  body+='<h2>Presentar a quienes están presentes</h2><p>Lee solo las apariciones que correspondan a lo ocurrido. Ajusta la postura y el lugar; detente si intervienen los jugadores.</p>'
  for a in cast:
   if a['name'] in presentations:body+='<details class="mr-cast-presentation"><summary>'+html.escape(a['name'])+'</summary><blockquote>'+''.join('<p>'+p+'</p>' for p in presentations[a['name']])+'</blockquote></details>'
  body+='<h2>Ambiente y efectos</h2><p>'+action('music',slug,'Iniciar / reanudar música instrumental')+' · '+action('quiet',slug,'Voz en primer plano')+'</p><p>'+' '.join(action('effect',s,next(x['name'] for x in audio if x['kind']=='sfx' and x['slug']==s)) for s in sfx)+'</p><p>'+action('stop-effects',slug,'Parar efectos y ambientes')+'</p>'
  if props:body+='<h2>Objetos y testimonios</h2><ul>'+''.join('<li>@UUID[Item.'+a['_id']+']{'+html.escape(a['name'])+'}</li>' for a in props)+'</ul>'
  body+='<h2>Notas para dirigir</h2>'+re.sub(r'<blockquote>.*?</blockquote>','',section['body'],flags=re.S)
  body+='<p>@UUID[JournalEntry.'+uid('edition-1.1/journal/'+d['chapter'])+'.JournalEntryPage.'+uid('edition-1.1/'+d['chapter']+'/'+str(d['section']))+']{Abrir la sección del manual}</p></section>'
  journals.append({'_id':jid,'name':'Escena · '+scene['name'],'folder':folder,'pages':[{'_id':pageid,'name':'Lectura y dirección','type':'text','text':{'format':1,'content':body}}],'ownership':{'default':0},'flags':flags('direction-'+slug)})
  scene.update(journal=jid,journalEntryPage=pageid,playlist=uid('playlist/music'),playlistSound=soundids['music/'+d['music']])
  scene['flags'][mod]['direction']={'journalId':jid,'pageId':pageid,'music':d['music'],'actors':[a['_id'] for a in cast],'effects':sfx,'items':[a['_id'] for a in props]}
 # Créditos accesibles dentro del propio módulo, no solo en GitHub.
 credits='<h2>Música instrumental</h2><p>Kevin MacLeod (incompetech.com). Creative Commons Attribution 4.0, https://creativecommons.org/licenses/by/4.0/. Piezas recortadas, adaptadas a bucle y normalizadas.</p><ul>'+''.join('<li>'+html.escape(d['name'])+' — «'+html.escape(d['title'])+'», Kevin MacLeod. <a href="'+d['source']+'">Ficha original</a>.</li>' for d in audio if d['kind']=='music')+'</ul><p>Los efectos de sonido se han sintetizado para el Proyecto MR, sin voces ni muestras externas.</p>'
 journals.append({'_id':uid('journal/audio-credits'),'name':'Créditos · Música y sonido','folder':folder,'pages':[{'_id':uid('page/audio-credits'),'name':'Atribución','type':'text','text':{'format':1,'content':credits}}],'ownership':{'default':2},'flags':flags('audio-credits','players')})
 return playlists
