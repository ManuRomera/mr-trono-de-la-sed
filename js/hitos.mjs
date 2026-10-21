/** Hitos de la investigación: el Narrador los marca y la mesa los ve, sin spoilers. */
const MOD='mr-trono-de-la-sed';
export const HITOS=Object.freeze(['funeral','ataud','registros','pluma','henut','pozo','invitacion','banquete','vivos','merit','camara','final']);
const E=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
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
   const li=e.target.closest('[data-hito]');if(!li||!game.user.isGM)return;
   const now=hitosState(game.settings.get(MOD,'hitos'));now[li.dataset.hito]=!now[li.dataset.hito];await game.settings.set(MOD,'hitos',now);
  });
 }
 pill.setAttribute('aria-expanded',String(!panel.hidden));pill.setAttribute('aria-label',ui_('Title'));
 pill.innerHTML=`<img src="modules/${MOD}/brand/MR_09_Monograma_Marfil_Transparente.png" alt="" draggable="false"><span>${E(ui_('Title'))}</span><b>${p.done}/${p.total}</b><i style="--p:${Math.round(100*p.done/p.total)}%"></i>`;
 panel.innerHTML=`<h3>${E(ui_('Title'))}</h3><p class="mr-hitos-help">${E(ui_(game.user.isGM?'HelpGM':'HelpPlayer'))}</p><ol>${HITOS.map(id=>`<li data-hito="${id}" class="${state[id]?'is-done':''}" ${game.user.isGM?'tabindex="0" role="button"':''} aria-pressed="${state[id]}"><span class="mr-hito-mark" aria-hidden="true">${state[id]?'✦':'·'}</span><span>${E(state[id]||game.user.isGM?label(id):ui_('Hidden'))}</span></li>`).join('')}</ol>`;
}
export function registerHitos(){
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
  if(setting.key!==`${MOD}.hitos`)return;
  const now=hitosState(setting.value);
  for(const id of HITOS)if(now[id]&&!last[id])ui.notifications.info(`${ui_('Unlocked')}: ${label(id)}`);
  last=now;
 });
 document.addEventListener('keydown',e=>{if(e.altKey&&e.code==='KeyH'&&pill){e.preventDefault();pill.click();}});
}
