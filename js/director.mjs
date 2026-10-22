import {presentationSettings,setPresentation,fitPresentation,figureLayout,stageLayout,stageFor,resizeFigures,visiblePresentationBounds} from './presentation.mjs';
/** Dirección de escena con documentos y audio nativos de Foundry v13. */
const MOD='mr-trono-de-la-sed';
const E=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const owned=d=>d?.getFlag?.(MOD,'source')===MOD;
let tail=Promise.resolve(),bar,refreshQueued=false;
const activeGM=()=>game.user.isGM&&(!game.users.activeGM||game.users.activeGM.id===game.user.id);
const label=key=>game.i18n.localize('MRTRONO.Director.'+key);
const sceneFor=slug=>game.scenes.find(s=>owned(s)&&s.getFlag(MOD,'slug')===slug);
const playlistFor=kind=>game.playlists.find(p=>owned(p)&&p.getFlag(MOD,'kind')===kind);
const direction=s=>s?.getFlag(MOD,'direction');
const soundFor=(pl,slug)=>pl?.sounds.find(s=>s.getFlag(MOD,'slug')===slug);
export const AMBIENTS=Object.freeze({light:{dark:0,level:.35},dim:{dark:.38,level:.3},dark:{dark:.72,level:.22}});
export function ambientFor(key){return AMBIENTS[key]??null;}
export function splitCommand(value){const at=value.indexOf('|');return at<0?null:{action:value.slice(0,at),arg:value.slice(at+1)};}
export function audioVolume(level,quiet){const n=Number(level);return Math.min(1,Math.max(0,Number.isFinite(n)?n:.3))*(quiet?.28:1);}
export function missingCast(existing,actors){const ids=new Set(existing.map(t=>t.actorId));return actors.filter(a=>!ids.has(a.id));}
function enqueue(fn){tail=tail.catch(()=>{}).then(fn);return tail;}
function warn(key){ui.notifications.warn(label(key));}
function mix(){return game.settings.get(MOD,'sceneMix')??{level:.3,quiet:false};}
function subject(){return owned(canvas?.scene)?canvas.scene:sceneFor(bar?.querySelector('select')?.value);}
export async function openSceneGuide(slug){
 if(!game.user.isGM)return;
 const s=slug?sceneFor(slug):subject();const d=direction(s);if(!d)return warn('ImportFirst');
 const doc=game.journal.get(d.journalId);if(doc)await doc.sheet.render(true,{pageId:d.pageId});else warn('ImportFirst');
}
/** Cambio de pista con fundido cruzado: la nueva entra antes de que la anterior salga (los dos fundidos, con la duración `fade` de cada sonido, se solapan). */
async function crossfadeTo(pl,sound){
 await sound.update({volume:audioVolume(mix().level,mix().quiet)});
 const leaving=pl.sounds.filter(o=>o.playing&&o.id!==sound.id);
 // playSound() espera a que termine su fundido de entrada: se lanza sin esperar para que entrada y salida corran a la vez.
 const volume=audioVolume(mix().level,mix().quiet),starting=!sound.playing;
 const entering=starting?pl.playSound(sound):Promise.resolve();
 const out=leaving.map(other=>pl.stopSound(other));
 // La entrada se rampa a mano con la misma duración que la salida, para que la suma de volúmenes se mantenga estable.
 if(starting&&leaving.length){for(let i=0;i<40&&!sound.sound?.playing;i++)await new Promise(r=>setTimeout(r,25));
  if(sound.sound){sound.sound.volume=0;sound.sound.fade(volume,{duration:Math.max(300,sound.fadeDuration||0)});}}
 await Promise.all([entering,...out]);
}
async function playMusic(slug){
 const scene=sceneFor(slug);const pl=playlistFor('music');const sound=soundFor(pl,direction(scene)?.music);if(!sound)return warn('ImportFirst');
 await crossfadeTo(pl,sound);
}
/** Motivos: pistas para un momento concreto (batalla, tensión…). Pulsar el activo devuelve a la música de la escena. */
async function playMotif(slug,sceneSlug){
 const pl=playlistFor('music');const sound=soundFor(pl,slug);if(!sound)return warn('ImportFirst');
 if(sound.playing&&sceneSlug)return playMusic(sceneSlug);
 await crossfadeTo(pl,sound);
}
async function stopAudio(){for(const kind of ['music','sfx']){const p=playlistFor(kind);if(p)await p.stopAll();}}
async function effect(slug){const p=playlistFor('sfx');const s=soundFor(p,slug);if(!s)return warn('ImportFirst');if(s.playing){await p.stopSound(s);if(s.repeat)return;}await p.playSound(s);}
async function applyMix(level,quiet){
 await game.settings.set(MOD,'sceneMix',{level,quiet});const p=playlistFor('music');if(p)await p.updateEmbeddedDocuments('PlaylistSound',p.sounds.contents.filter(s=>s.playing).map(s=>({_id:s.id,volume:audioVolume(level,quiet)})));
}
async function placeActors(scene,actors){
 if(!scene)return warn('ImportFirst');
 const pending=missingCast(scene.tokens.contents,actors);if(!pending.length)return ui.notifications.info(label('AlreadyPlaced'));
 const docs=[];const settings=presentationSettings();const stage=settings.depthScale?stageFor(scene):null;const bounds=visiblePresentationBounds(scene);const positions=stage?stageLayout(scene,pending.length,scene.tokens.size,settings.tokenPixels,stage,bounds):figureLayout(scene,pending.length,scene.tokens.size,settings.tokenPixels,bounds);
 for(let i=0;i<pending.length;i++){
  const actor=pending[i];const token=await actor.getTokenDocument({...positions[i],flags:{[MOD]:{placed:true}},lockRotation:settings.lockRotation,actorLink:actor.type==='litm-character'||!['Custodios de la corte','Servidores sin nombre','Sombras de chacal','Borrados','Plañideras','Pesadores'].includes(actor.name)});docs.push(token.toObject());
 }
 await scene.createEmbeddedDocuments('Token',docs);
}
export async function dispatchDirector(action,arg=''){
 const readOnly=['read','actor','book','view','fit','recenter','compact'];
 if(!game.user.isGM)return false;
 if(!readOnly.includes(action)&&!activeGM()){warn('ActiveGM');return false;}
 if(action==='fit'){fitPresentation();return true;}
 if(action==='recenter'){await game.settings.set(MOD,'directorPos',null);applyBarPosition();return true;}
 if(action==='compact'){await game.settings.set(MOD,'directorCompact',!game.settings.get(MOD,'directorCompact'));refreshDirector();return true;}
 if(action==='read'){await openSceneGuide(arg);return true;}
 if(action==='actor'){const a=game.actors.find(a=>owned(a)&&a.getFlag(MOD,'slug')===arg);if(a)await a.sheet.render({force:true});return !!a;}
 if(action==='book'){game.modules.get(MOD).api.openGMBook();return true;}
 if(action==='view'){await sceneFor(arg)?.view();return true;}
 const valid=['activate','music','quiet','stop','stop-effects','effect','heroes','token','level','presentation','resize','resize-selected','ambient','motif'];if(!valid.includes(action))return false;
 return enqueue(async()=>{
  if(!activeGM())return false;
  if(action==='presentation'){const [key,value]=arg.split('~');await setPresentation(key,key==='tokenPixels'?Number(value):value==='true');}
  if(action==='resize'||action==='resize-selected')await resizeFigures(sceneFor(arg),action==='resize-selected');
  if(action==='activate'){const s=sceneFor(arg);if(!s)return false;await s.activate();const linked=typeof s.playlist==='string'?s.playlist:s.playlist?.id;if(!linked||linked===playlistFor('music')?.id)await playMusic(arg);}
  if(action==='music')await playMusic(arg);
  if(action==='motif'){const [m,sc]=arg.split('~');await playMotif(m,sc);}
  if(action==='quiet'){const m=mix();await applyMix(m.level,!m.quiet);}
  if(action==='level')await applyMix(Number(arg),mix().quiet);
  if(action==='ambient'){const [slug,key]=arg.split('~');const sc=sceneFor(slug),a=ambientFor(key);if(sc&&a){await sc.update({'environment.darknessLevel':a.dark,[`flags.${MOD}.ambient`]:key});await applyMix(a.level,false);}}
  if(action==='stop')await stopAudio();
  if(action==='stop-effects')await playlistFor('sfx')?.stopAll();
  if(action==='effect')await effect(arg);
  if(action==='heroes')await placeActors(sceneFor(arg),game.actors.filter(a=>owned(a)&&a.type==='litm-character'));
  if(action==='token'){const [slug,person]=arg.split('~');const a=game.actors.find(a=>owned(a)&&a.getFlag(MOD,'slug')===person);if(a)await placeActors(sceneFor(slug),[a]);}
  refreshDirector();return true;
 });
}
function control(action,arg,text,icon,extra='',cls=''){return `<button type="button" class="mr-btn ${cls}" data-trono-action="${action}" data-trono-arg="${E(arg)}" title="${E(text)}" ${extra}><i class="fa-solid fa-${icon}" aria-hidden="true"></i><span>${E(text)}</span></button>`;}
const MARK=`modules/${MOD}/brand/MR_09_Monograma_Marfil_Transparente.png`;
export function refreshDirector(){
 if(refreshQueued)return;refreshQueued=true;
 queueMicrotask(()=>{refreshQueued=false;renderDirector();});
}
/** Posición de la barra: se arrastra con el botón derecho y se recuerda por usuario. */
export function clampBar(pos,size,view){return {x:Math.round(Math.min(Math.max(0,view[0]-size[0]),Math.max(0,pos.x))),y:Math.round(Math.min(Math.max(0,view[1]-size[1]),Math.max(0,pos.y)))};}
function applyBarPosition(){
 if(!bar)return;const pos=game.settings.get(MOD,'directorPos');
 if(!pos||!Number.isFinite(pos.x)||!Number.isFinite(pos.y)){bar.style.left='';bar.style.top='';bar.style.transform='';bar.classList.remove('is-placed');return;}
 const r=bar.getBoundingClientRect(),c=clampBar(pos,[r.width,r.height],[innerWidth,innerHeight]);
 bar.style.left=c.x+'px';bar.style.top=c.y+'px';bar.style.transform='none';bar.classList.add('is-placed');
}
function enableDrag(){
 let drag=null;
 bar.addEventListener('contextmenu',e=>e.preventDefault());
 bar.addEventListener('pointerdown',e=>{
  if(e.button!==2)return;e.preventDefault();const r=bar.getBoundingClientRect();
  drag={dx:e.clientX-r.left,dy:e.clientY-r.top,id:e.pointerId};bar.setPointerCapture(e.pointerId);bar.classList.add('is-dragging');
 });
 bar.addEventListener('pointermove',e=>{
  if(!drag||e.pointerId!==drag.id)return;const r=bar.getBoundingClientRect();
  const c=clampBar({x:e.clientX-drag.dx,y:e.clientY-drag.dy},[r.width,r.height],[innerWidth,innerHeight]);
  bar.style.left=c.x+'px';bar.style.top=c.y+'px';bar.style.transform='none';bar.classList.add('is-placed');
 });
 const end=e=>{
  if(!drag||(e.pointerId!==undefined&&e.pointerId!==drag.id))return;drag=null;bar.classList.remove('is-dragging');
  const r=bar.getBoundingClientRect();game.settings.set(MOD,'directorPos',{x:Math.round(r.left),y:Math.round(r.top)});
 };
 bar.addEventListener('pointerup',end);bar.addEventListener('pointercancel',end);
 window.addEventListener('resize',applyBarPosition);
}
function renderDirector(){
 if(!game.user.isGM||!game.settings.get(MOD,'directorVisible')){bar?.remove();bar=null;return;}
 const scenes=game.scenes.filter(owned);if(!scenes.length){bar?.remove();bar=null;return;}
 const selected=subject()??scenes[0];const slug=selected.getFlag(MOD,'slug');const d=direction(selected);if(!d)return;
 if(!bar){bar=document.createElement('aside');bar.id='mr-trono-director';bar.setAttribute('aria-label',label('Title'));bar.setAttribute('role','region');document.body.append(bar);
  document.addEventListener('pointerdown',e=>{if(!bar)return;for(const d of bar.querySelectorAll('details[open]'))if(!d.contains(e.target))d.open=false;},true);
  bar.addEventListener('click',e=>{const b=e.target.closest('[data-trono-action]');if(!b)return;e.preventDefault();dispatchDirector(b.dataset.tronoAction,b.dataset.tronoArg).catch(reportError);});
  bar.addEventListener('change',e=>{if(e.target.matches('.mr-director-scenes'))dispatchDirector('view',e.target.value).catch(reportError);if(e.target.matches('input[type=range]'))dispatchDirector('level',e.target.value).catch(reportError);if(e.target.dataset.presentation)dispatchDirector('presentation',e.target.dataset.presentation+'~'+(e.target.type==='checkbox'?e.target.checked:e.target.value)).catch(reportError);});
  enableDrag();
 }
 const openMenus=new Set([...bar.querySelectorAll('details[open]')].map(x=>x.dataset.menu));
 const options=presentationSettings();const compact=!!game.settings.get(MOD,'directorCompact');
 const music=soundFor(playlistFor('music'),d.music);const isPlaying=!!music?.playing;const m=mix();
 const motifs=(playlistFor('music')?.sounds.contents??[]).filter(x=>x.getFlag(MOD,'motif'));
 const motifMenu=motifs.length?`<details data-menu="motifs"><summary class="mr-btn"><i class="fa-solid fa-wave-square" aria-hidden="true"></i><span>${E(label('Motifs'))}</span></summary><div class="mr-director-menu mr-motifs-menu"><p><strong>${E(label('Motifs'))}</strong></p><p class="mr-director-status">${E(label('MotifsHelp'))}</p><div class="mr-motif-grid">${motifs.map(x=>control('motif',x.getFlag(MOD,'slug')+'~'+slug,x.name,'music',`aria-pressed="${!!x.playing}"`,'mr-motif')).join('')}</div></div></details>`:'';
 bar.classList.toggle('is-compact',compact);bar.classList.toggle('no-bg',!game.settings.get(MOD,'directorBg'));bar.classList.toggle('is-glass',game.settings.get(MOD,'directorStyle')==='glass');
 bar.innerHTML=`<div class="mr-director-head"><div class="mr-grip" title="${E(label('DragHint'))}"><img class="mr-mark" src="${MARK}" alt="MR" draggable="false"><span class="mr-title"><b>${E(label('Direction'))}</b><small>${E(label('Title'))}</small></span></div><select class="mr-director-scenes" aria-label="${E(label('ChooseScene'))}">${scenes.map(s=>`<option value="${E(s.getFlag(MOD,'slug'))}" ${s.id===selected.id?'selected':''}>${E(s.name)}</option>`).join('')}</select><div class="mr-grp">${control('read',slug,label('Read'),'book-open')}${control('activate',slug,label('Show'),'panorama','','is-primary')}</div><div class="mr-grp mr-secondary">${control('music',slug,label(isPlaying?'Resume':'Music'),'music')}${motifMenu}${control('quiet',slug,label('Quiet'),'volume-low',`aria-pressed="${m.quiet}"`)}${control('stop',slug,label('Stop'),'volume-xmark')}</div><div class="mr-grp mr-secondary">${control('fit',slug,label('Fit'),'expand')}<details data-menu="figures"><summary class="mr-btn"><i class="fa-solid fa-people-group" aria-hidden="true"></i><span>${E(label('Figures'))}</span></summary><div class="mr-director-menu mr-figures-menu"><p><strong>${E(label('Figures'))}</strong></p><label>${E(label('TokenSize'))}<input type="number" data-presentation="tokenPixels" min="60" max="900" step="10" value="${options.tokenPixels}"></label><p class="mr-director-status">${E(label('TokenSizeHelp'))}</p><p>${[240,360,480].map(n=>control('presentation','tokenPixels~'+n,n+' px','person')).join(' ')}</p><p>${control('resize-selected',slug,label('ResizeSelected'),'up-right-and-down-left-from-center')} ${control('resize',slug,label('ResizeAll'),'people-group')}</p><label><input type="checkbox" data-presentation="depthScale" ${options.depthScale?'checked':''}> ${E(label('DepthScale'))}</label><p class="mr-director-status">${E(label('DepthScaleHelp'))}</p><label><input type="checkbox" data-presentation="lockRotation" ${options.lockRotation?'checked':''}> ${E(label('LockRotation'))}</label><label><input type="checkbox" data-presentation="hideTrails" ${options.hideTrails?'checked':''}> ${E(label('HideTrails'))}</label><label><input type="checkbox" data-presentation="cover" ${options.cover?'checked':''}> ${E(label('Cover'))}</label></div></details><details data-menu="mix"><summary class="mr-btn mr-icon" aria-label="${E(label('More'))}"><i class="fa-solid fa-sliders" aria-hidden="true"></i></summary><div class="mr-director-menu"><p>${E(label('Mix'))}</p><label>${E(label('Level'))}<input type="range" min="0" max="1" step=".05" value="${E(m.level)}"></label><p class="mr-director-status">${E(music?.name??'')} · ${E(label(isPlaying?'Playing':'Stopped'))}</p><p>${control('heroes',slug,label('Heroes'),'people-group')}${control('book','',label('Book'),'ankh')}</p><p><strong>${E(game.i18n.localize('MRTRONO.Ambient.Title'))}</strong></p><p>${['light','dim','dark'].map(k=>control('ambient',slug+'~'+k,game.i18n.localize('MRTRONO.Ambient.'+k.charAt(0).toUpperCase()+k.slice(1)),{light:'sun',dim:'cloud-moon',dark:'moon'}[k],`aria-pressed="${selected.getFlag(MOD,'ambient')===k}"`)).join('')}</p><p>${control('stop-effects',slug,label('StopEffects'),'stop')}${control('recenter','',label('Recenter'),'arrows-to-dot')}</p><p class="mr-director-status">${E(label('DragHint'))}</p></div></details></div><button type="button" class="mr-btn mr-icon mr-collapse" data-trono-action="compact" data-trono-arg="" aria-pressed="${compact}" title="${E(label(compact?'Expand':'Compact'))}"><i class="fa-solid fa-${compact?'chevron-down':'chevron-up'}" aria-hidden="true"></i></button></div><div class="mr-director-cues">${d.effects.map(s=>{const snd=soundFor(playlistFor('sfx'),s);return control('effect',s,snd?.name??s,'wave-square',`aria-pressed="${!!snd?.playing}"`,'mr-chip');}).join('')}</div>`;
 for(const b of bar.querySelectorAll('.mr-btn:not([title])')){const t=b.textContent.trim();if(t)b.title=t;}
 for(const menu of bar.querySelectorAll('details'))menu.open=openMenus.has(menu.dataset.menu);
 applyBarPosition();
}
function reportError(error){console.error(`${MOD} | direction`,error);ui.notifications.error(label('Error'));}
export function setupDirector(){
 if(!globalThis.document?.createElement)return;
 refreshDirector();
 for(const h of ['mrTronoPresentationChanged','canvasReady','updateScene','createScene','deleteScene','updatePlaylist','updatePlaylistSound','createPlaylist'])Hooks.on(h,refreshDirector);
 // Sincroniza el volumen de lectura también cuando la reproducción empieza por enlace nativo de escena.
 Hooks.on('updateScene',(scene,changes)=>{const linked=typeof scene.playlist==='string'?scene.playlist:scene.playlist?.id;if(changes.active&&owned(scene)&&activeGM()&&linked===playlistFor('music')?.id)dispatchDirector('music',scene.getFlag(MOD,'slug')).catch(reportError);});
}
export function registerDirector(){
 game.settings.register(MOD,'directorVisible',{name:'MRTRONO.Director.Visible',hint:'MRTRONO.Director.VisibleHelp',scope:'client',config:true,type:Boolean,default:true,onChange:refreshDirector});
 game.settings.register(MOD,'directorBg',{name:'MRTRONO.Director.Bg',hint:'MRTRONO.Director.BgHelp',scope:'client',config:true,type:Boolean,default:true,onChange:refreshDirector});
 game.settings.register(MOD,'directorStyle',{name:'MRTRONO.Director.Style',hint:'MRTRONO.Director.StyleHelp',scope:'client',config:true,type:String,default:'classic',choices:{classic:'MRTRONO.Director.StyleClassic',glass:'MRTRONO.Director.StyleGlass'},onChange:refreshDirector});
 game.settings.register(MOD,'sceneMix',{scope:'world',config:false,type:Object,default:{level:.3,quiet:false}});
 game.settings.register(MOD,'directorPos',{scope:'client',config:false,type:Object,default:null});
 game.settings.register(MOD,'directorCompact',{scope:'client',config:false,type:Boolean,default:false});
 const enrichers=globalThis.CONFIG?.TextEditor?.enrichers;
 if(!enrichers||!globalThis.document?.addEventListener)return;
 enrichers.push({id:MOD+'-direction',pattern:/@Trono\[([^\]]+)\](?:\{([^}]+)\})?/g,enricher:async match=>{
  const command=splitCommand(match[1]);if(!command||!game.user.isGM)return document.createElement('span');
  const a=document.createElement('a');a.className='mr-trono-cue';a.dataset.tronoAction=command.action;a.dataset.tronoArg=command.arg;a.setAttribute('role','button');a.setAttribute('tabindex','0');a.textContent=match[2]??command.action;return a;
 }});
 const act=e=>{const a=e.target.closest?.('.mr-trono-cue');if(!a)return;if(e.type==='keydown'&&!['Enter',' '].includes(e.key))return;e.preventDefault();e.stopPropagation();dispatchDirector(a.dataset.tronoAction,a.dataset.tronoArg).catch(reportError);};
 document.addEventListener('click',act,true);document.addEventListener('keydown',act,true);
}
