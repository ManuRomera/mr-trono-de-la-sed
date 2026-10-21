/** Hitos de la investigación: el Narrador los marca y la mesa los ve, sin spoilers. */
const MOD='mr-trono-de-la-sed';
export const HITOS=Object.freeze(['funeral','ataud','registros','pluma','henut','pozo','invitacion','banquete','vivos','merit','camara','final']);
const E=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const LAMPS=7;
export function lampsValue(v){const n=Number(v);return Number.isFinite(n)?Math.min(LAMPS,Math.max(0,Math.round(n))):LAMPS;}
export function lampsAfterClick(current,index){const c=lampsValue(current);return index<c?index:index+1;}
export function lampsStage(n){const c=lampsValue(n);return c>=5?'7':c===4?'4':c===3?'3':c===2?'2':c===1?'1':'0';}
export function hitosState(value){const out={};for(const id of HITOS)out[id]=!!value?.[id];return out;}
export function hitosProgress(value){const s=hitosState(value);const done=HITOS.filter(id=>s[id]).length;return {done,total:HITOS.length};}
const label=id=>game.i18n.localize('MRTRONO.Hitos.'+id);
const ui_=key=>game.i18n.localize('MRTRONO.Hitos.'+key);
let pill,panel;
const hasAdventure=()=>game.scenes?.some(s=>s.getFlag(MOD,'source')===MOD);
function render(){
 if(!hasAdventure()){pill?.remove();panel?.remove();pill=panel=null;return;}
 const state=hitosState(game.settings.get(MOD,'hitos')),p=hitosProgress(state);
 if(!pill){
  pill=document.createElement('button');pill.type='button';pill.id='mr-trono-hitos';document.body.append(pill);
  pill.addEventListener('click',()=>{panel.hidden=!panel.hidden;pill.setAttribute('aria-expanded',String(!panel.hidden));});
  panel=document.createElement('aside');panel.id='mr-trono-hitos-panel';panel.hidden=true;panel.setAttribute('role','region');document.body.append(panel);
  panel.addEventListener('click',async e=>{
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
 panel.innerHTML=lampHtml+`<h3>${E(ui_('Title'))}</h3><p class="mr-hitos-help">${E(ui_(game.user.isGM?'HelpGM':'HelpPlayer'))}</p><ol>${HITOS.map(id=>`<li data-hito="${id}" class="${state[id]?'is-done':''}" ${game.user.isGM?'tabindex="0" role="button"':''} aria-pressed="${state[id]}"><span class="mr-hito-mark" aria-hidden="true">${state[id]?'✦':'·'}</span><span>${E(state[id]||game.user.isGM?label(id):ui_('Hidden'))}</span></li>`).join('')}</ol>`;
}
export function registerHitos(){
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
