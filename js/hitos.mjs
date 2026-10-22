/** Hitos de la investigación: el Narrador los marca y la mesa los ve, sin spoilers. */
const MOD='mr-trono-de-la-sed';
export const HITOS=Object.freeze(['funeral','ataud','registros','pluma','henut','pozo','invitacion','banquete','vivos','merit','camara','final']);
const E=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const LAMPS=7;
/** Posición libre de la insignia: se arrastra con el botón derecho y se recuerda por usuario. */
export function clampPill(pos,size,view){return {x:Math.round(Math.min(Math.max(0,view[0]-size[0]),Math.max(0,pos.x))),y:Math.round(Math.min(Math.max(0,view[1]-size[1]),Math.max(0,pos.y)))};}
export function panelSide(pill,view){return pill.y>view[1]/2?'above':'below';}
export function lampsValue(v){const n=Number(v);return Number.isFinite(n)?Math.min(LAMPS,Math.max(0,Math.round(n))):LAMPS;}
export function lampsAfterClick(current,index){const c=lampsValue(current);return index<c?index:index+1;}
export function lampsStage(n){const c=lampsValue(n);return c>=5?'7':c===4?'4':c===3?'3':c===2?'2':c===1?'1':'0';}
export function hitosState(value){const out={};for(const id of HITOS)out[id]=!!value?.[id];return out;}
export function hitosProgress(value){const s=hitosState(value);const done=HITOS.filter(id=>s[id]).length;return {done,total:HITOS.length};}
const label=id=>game.i18n.localize('MRTRONO.Hitos.'+id);
const ui_=key=>game.i18n.localize('MRTRONO.Hitos.'+key);
let pill,panel;
const hasAdventure=()=>game.scenes?.some(s=>s.getFlag(MOD,'source')===MOD);
function placePill(){
 if(!pill)return;const pos=game.settings.get(MOD,'hitosPos');
 if(!pos||!Number.isFinite(pos.x)||!Number.isFinite(pos.y)){pill.style.left='';pill.style.top='';pill.style.bottom='';pill.classList.remove('is-placed');}
 else{const r=pill.getBoundingClientRect(),c=clampPill(pos,[r.width,r.height],[innerWidth,innerHeight]);drag.pos=c;pill.style.left=c.x+'px';pill.style.top=c.y+'px';pill.style.bottom='auto';pill.classList.add('is-placed');}
 placePanel();
}
function placePanel(){
 if(!pill||!panel)return;const r=pill.getBoundingClientRect(),pw=panel.offsetWidth||310,ph=panel.offsetHeight||360;
 const left=Math.min(Math.max(8,r.left),Math.max(8,innerWidth-pw-8));panel.style.left=left+'px';
 if(panelSide({x:r.left,y:r.top},[innerWidth,innerHeight])==='above'){panel.style.bottom=(innerHeight-r.top+8)+'px';panel.style.top='auto';}
 else{panel.style.top=(r.bottom+8)+'px';panel.style.bottom='auto';}
}
function enableDrag(){
 let drag=null;
 pill.addEventListener('contextmenu',e=>e.preventDefault());
 pill.addEventListener('pointerdown',e=>{if(e.button!==2)return;e.preventDefault();const r=pill.getBoundingClientRect();drag={dx:e.clientX-r.left,dy:e.clientY-r.top,id:e.pointerId,moved:false};try{pill.setPointerCapture(e.pointerId);}catch{}pill.classList.add('is-dragging');});
 pill.addEventListener('pointermove',e=>{if(!drag||e.pointerId!==drag.id)return;drag.moved=true;const r=pill.getBoundingClientRect(),c=clampPill({x:e.clientX-drag.dx,y:e.clientY-drag.dy},[r.width,r.height],[innerWidth,innerHeight]);drag.pos=c;pill.style.left=c.x+'px';pill.style.top=c.y+'px';pill.style.bottom='auto';pill.classList.add('is-placed');placePanel();});
 const end=e=>{if(!drag||(e.pointerId!==undefined&&e.pointerId!==drag.id))return;const moved=drag.moved,pos=drag.pos;drag=null;pill.classList.remove('is-dragging');if(!moved||!pos)return;game.settings.set(MOD,'hitosPos',{x:Math.round(pos.x),y:Math.round(pos.y)});};
 pill.addEventListener('pointerup',end);pill.addEventListener('pointercancel',end);
 window.addEventListener('resize',placePill);
}
function render(){
 if(!hasAdventure()){pill?.remove();panel?.remove();pill=panel=null;return;}
 const state=hitosState(game.settings.get(MOD,'hitos')),p=hitosProgress(state);
 if(!pill){
  pill=document.createElement('button');pill.type='button';pill.id='mr-trono-hitos';document.body.append(pill);
  pill.addEventListener('click',()=>{panel.hidden=!panel.hidden;pill.setAttribute('aria-expanded',String(!panel.hidden));placePanel();});
  enableDrag();
  panel=document.createElement('aside');panel.id='mr-trono-hitos-panel';panel.hidden=true;panel.setAttribute('role','region');document.body.append(panel);
  panel.addEventListener('click',async e=>{
   if(e.target.closest('[data-reset-pos]')){await game.settings.set(MOD,'hitosPos',null);placePill();return;}
   const lamp=e.target.closest('[data-lamp]');
   if(lamp&&game.user.isGM){await game.settings.set(MOD,'lamparas',lampsAfterClick(game.settings.get(MOD,'lamparas'),Number(lamp.dataset.lamp)));return;}
   const li=e.target.closest('[data-hito]');if(!li||!game.user.isGM)return;
   const now=hitosState(game.settings.get(MOD,'hitos'));now[li.dataset.hito]=!now[li.dataset.hito];await game.settings.set(MOD,'hitos',now);
  });
 }
 pill.setAttribute('aria-expanded',String(!panel.hidden));pill.setAttribute('aria-label',ui_('Title'));
 pill.innerHTML=`<img src="modules/${MOD}/brand/MR_09_Monograma_Marfil_Transparente.png" alt="" draggable="false"><span>${E(ui_('Title'))}</span><b>${p.done}/${p.total}</b><i style="--p:${Math.round(100*p.done/p.total)}%"></i>`;
 const lamps=lampsValue(game.settings.get(MOD,'lamparas'));
 const lampHtml=game.user.isGM?`<div class="mr-lamps"><h3>${E(ui_('LampsTitle'))}</h3><div class="mr-lamp-row">${Array.from({length:LAMPS},(_,i)=>`<button type="button" class="mr-lamp ${i<lamps?'is-lit':''}" data-lamp="${i}" aria-label="${i+1}" aria-pressed="${i<lamps}"><span></span></button>`).join('')}</div><p class="mr-hitos-help"><b>${lamps}/7.</b> ${E(game.i18n.localize('MRTRONO.Hitos.Lamp'+lampsStage(lamps)))}</p></div>`:'';
 panel.innerHTML=lampHtml+`<h3>${E(ui_('Title'))}</h3><p class="mr-hitos-help">${E(ui_(game.user.isGM?'HelpGM':'HelpPlayer'))}</p><ol>${HITOS.map(id=>`<li data-hito="${id}" class="${state[id]?'is-done':''}" ${game.user.isGM?'tabindex="0" role="button"':''} aria-pressed="${state[id]}"><span class="mr-hito-mark" aria-hidden="true">${state[id]?'✦':'·'}</span><span>${E(state[id]||game.user.isGM?label(id):ui_('Hidden'))}</span></li>`).join('')}</ol><p class="mr-hitos-help mr-hitos-drag">${E(ui_('DragHint'))} <a href="#" data-reset-pos>${E(ui_('ResetPos'))}</a></p>`;
 placePill();
}
export function registerHitos(){
 game.settings.register(MOD,'hitosPos',{scope:'client',config:false,type:Object,default:null});
 game.settings.register(MOD,'lamparas',{scope:'world',config:false,type:Number,default:LAMPS,onChange:()=>render()});
 game.settings.register(MOD,'hitos',{scope:'world',config:false,type:Object,default:{},onChange:(value,options,userId)=>{
  render();
 }});
}
export function setupHitos(){
 if(!globalThis.document?.createElement)return;
 render();
 for(const h of ['canvasReady','createScene','deleteScene'])Hooks.on(h,render);
 let last=hitosState(game.settings.get(MOD,'hitos'));
 Hooks.on('renderSettings',()=>{});
 // Aviso a la mesa cuando se desbloquea un hito nuevo.
 Hooks.on('updateSetting',setting=>{
  if(setting.key===`${MOD}.lamparas`){if(game.user.isGM)ui.notifications.info(`${ui_('LampsTitle')}: ${lampsValue(setting.value)}/7 · ${game.i18n.localize('MRTRONO.Hitos.Lamp'+lampsStage(setting.value))}`);return;}
  if(setting.key!==`${MOD}.hitos`)return;
  const now=hitosState(setting.value);
  for(const id of HITOS)if(now[id]&&!last[id])ui.notifications.info(`${ui_('Unlocked')}: ${label(id)}`);
  last=now;
 });
 document.addEventListener('keydown',e=>{if(e.altKey&&e.code==='KeyH'&&pill){e.preventDefault();pill.click();}});
}
