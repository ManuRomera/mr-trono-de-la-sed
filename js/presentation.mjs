/** Encuadre panorámico y figuras: ajustes limitados a las escenas de esta aventura. */
const MOD='mr-trono-de-la-sed';
const owned=s=>s?.getFlag?.(MOD,'source')===MOD;
const activeGM=()=>game.user.isGM&&(!game.users.activeGM||game.users.activeGM.id===game.user.id);
export const DEFAULT_PRESENTATION=Object.freeze({tokenPixels:360,lockRotation:true,hideTrails:true,cover:true,depthScale:true});
export function presentationOptions(value={}){
 const pixels=Number(value.tokenPixels);
 return {tokenPixels:Math.round(Math.min(900,Math.max(60,Number.isFinite(pixels)?pixels:360))),lockRotation:value.lockRotation!==false,hideTrails:value.hideTrails!==false,cover:value.cover!==false,depthScale:value.depthScale!==false};
}
export function presentationSettings(){return presentationOptions(game.settings.get(MOD,'presentation'));}
/** Un zoom de cobertura conserva las proporciones. El paneo queda dentro de la ilustración. */
export function coverPosition(rect,screen,position={},center=false){
 if(!(rect.width>0&&rect.height>0&&screen[0]>0&&screen[1]>0))return null;
 const minimum=Math.max(screen[0]/rect.width,screen[1]/rect.height);
 const scale=center?minimum:Math.max(minimum,Number(position.scale)||minimum);
 const halfX=screen[0]/(2*scale),halfY=screen[1]/(2*scale);
 const clamp=(n,min,max)=>Math.min(max,Math.max(min,n));
 return {scale,x:clamp(center?rect.x+rect.width/2:(Number.isFinite(Number(position.x))?Number(position.x):rect.x+rect.width/2),rect.x+halfX,rect.x+rect.width-halfX),y:clamp(center?rect.y+rect.height/2:(Number.isFinite(Number(position.y))?Number(position.y):rect.y+rect.height/2),rect.y+halfY,rect.y+rect.height-halfY)};
}
/** Profundidad de escena: cada fondo declara su banda de suelo (content/stage.json) y las figuras escalan con ella. */
export const FOOT=0.055; // margen transparente bajo los pies en los tokens de cuerpo entero
let STAGES={};
export async function loadStages(){
 try{const r=await fetch(`modules/${MOD}/content/stage.json`);if(r.ok){const j=await r.json();delete j._nota;STAGES=j;}}catch(e){console.warn(`${MOD} | sin datos de profundidad`,e);}
}
export function stageFor(scene){return owned(scene)?(STAGES[scene.getFlag(MOD,'slug')]??null):null;}
export function setStages(value){STAGES=value;}
const clamp=(n,min,max)=>Math.min(max,Math.max(min,n));
/** Perspectiva: la cabeza de una persona de pie queda en la línea de horizonte (eye), así que su altura en pantalla es (pies − eye) × alto.
 *  El token mide más que la figura (margen transparente arriba y abajo); `pixels` (360 por defecto) escala todo el reparto a la vez. */
export const VISIBLE=.885;
export function figureSize(stage,footY,height,pixels=360,width=Infinity){
 const base=Math.max(.02,footY/height-stage.eye)*height/VISIBLE;
 return Math.min(900,width,height,Math.max(60,base*(pixels/360)));
}
export function depthFactor(stage,footY,height){return figureSize(stage,footY,height,360)/360;}
const DEPTHS=[.8,.25,.62,.08,.5,.95,.35,.7];
export function stageLayout(scene,count,start,pixels,stage,bounds={x:0,y:0,width:scene.width,height:scene.height}){
 const unit=scene.grid.size||100,anchors=stage.anchors??[];
 return Array.from({length:count},(_,i)=>{
  const j=start+i,a=anchors[j%Math.max(1,anchors.length)];
  const jitter=Math.floor(j/Math.max(1,anchors.length))*.035; // si hay más figuras que puntos, se desplazan un poco sin salir del suelo
  const fx=a?a[0]+jitter:.3+((j*.137)%.5),fy=a?a[1]:.9;
  const feet=fy*scene.height,cx=fx*scene.width;
  const size=figureSize(stage,feet,scene.height,pixels,bounds.width);
  return {x:clamp(cx-size/2,bounds.x,bounds.x+bounds.width-size),y:clamp(feet-size*(1-FOOT),bounds.y,bounds.y+bounds.height-size),width:size/unit,height:size/unit};
 });
}
/** Reajusta una figura a su profundidad conservando el centro y la línea de los pies. */
export function depthPatch(scene,token,pixels,stage,pos={}){
 const unit=scene.grid.size||100,size0=token.width*unit,h0=token.height*unit;
 const x=pos.x??token.x,y=pos.y??token.y,cx=x+size0/2,feet=y+h0*(1-FOOT);
 const size=figureSize(stage,feet,scene.height,pixels,scene.width);
 return {width:size/unit,height:size/unit,x:cx-size/2,y:feet-size*(1-FOOT)};
}
let adjusting=false;
export function fitPresentation(center=true){
 if(adjusting||!globalThis.canvas?.ready||!owned(canvas.scene)||!presentationSettings().cover)return;
 const p=coverPosition(canvas.dimensions.sceneRect,canvas.screenDimensions,{x:canvas.stage.pivot.x,y:canvas.stage.pivot.y,scale:canvas.stage.scale.x},center);if(!p)return;
 const old={x:canvas.stage.pivot.x,y:canvas.stage.pivot.y,scale:canvas.stage.scale.x};
 if(['x','y','scale'].every(k=>Math.abs(old[k]-p[k])<.00001))return;
 adjusting=true;try{canvas.pan(p);}finally{adjusting=false;}
}
/** Posiciones visibles de izquierda a derecha; tamaño expresado en píxeles de la escena. */
export function figureLayout(scene,count,start=0,pixels=360,bounds={x:0,y:0,width:scene.width,height:scene.height}){
 const size=Math.min(presentationOptions({tokenPixels:pixels}).tokenPixels,bounds.width,bounds.height);
 const gap=Math.max(12,size*.08),slots=Math.max(6,start+count),step=(bounds.width-size)/Math.max(1,slots-1);
 // Las transparencias permiten superponer cajas sin apilar personas sobre columnas o muebles.
 return Array.from({length:count},(_,i)=>({x:bounds.x+Math.min(bounds.width-size,(start+i)*step),y:bounds.y+Math.max(0,bounds.height-size-gap),width:size/(scene.grid.size||100),height:size/(scene.grid.size||100)}));
}
/** La fila nace dentro del encuadre visible, también en pantallas 4:3 o ultrapanorámicas. */
export function visiblePresentationBounds(scene){
 if(!globalThis.canvas?.ready||canvas.scene?.id!==scene.id)return undefined;
 const rect=canvas.dimensions.sceneRect,scale=canvas.stage.scale.x,screen=canvas.screenDimensions;
 const x=Math.max(0,canvas.stage.pivot.x-screen[0]/(2*scale)-rect.x),y=Math.max(0,canvas.stage.pivot.y-screen[1]/(2*scale)-rect.y);
 return {x,y,width:Math.min(scene.width-x,screen[0]/scale),height:Math.min(scene.height-y,screen[1]/scale)};
}
function refreshFigures(){
 if(!globalThis.canvas?.ready)return;
 for(const token of [...(canvas.tokens?.placeables??[]),...(canvas.tokens?.preview?.children??[])])token.renderFlags?.set({refreshState:true,refreshRuler:true});
}
export async function setPresentation(key,value){
 if(!activeGM()||!Object.hasOwn(DEFAULT_PRESENTATION,key))return false;
 const next=presentationOptions({...presentationSettings(),[key]:value});
 await game.settings.set(MOD,'presentation',next);
 // El bloqueo nativo se aplica a las figuras ya presentes, sin cambiar su tamaño ni posición.
 if(key==='lockRotation')for(const scene of game.scenes.filter(owned)){
  const updates=scene.tokens.contents.filter(t=>t.lockRotation!==next.lockRotation).map(t=>({_id:t.id,lockRotation:next.lockRotation}));
  if(updates.length)await scene.updateEmbeddedDocuments('Token',updates);
 }
 return true;
}
export async function resizeFigures(scene,selected=false){
 if(!activeGM()||!owned(scene))return false;
 const ids=selected?new Set((canvas.tokens?.controlled??[]).map(t=>t.id)):null;
 const pixels=presentationSettings().tokenPixels,unit=scene.grid.size||100,stage=presentationSettings().depthScale?stageFor(scene):null;
 const changes=scene.tokens.contents.filter(t=>!ids||ids.has(t.id)).map(t=>{
  if(stage)return {_id:t.id,...depthPatch(scene,t,pixels,stage)};
  const size=Math.min(pixels,scene.height,scene.width),oldSize=t.width*unit,oldHeight=t.height*unit;
  return {_id:t.id,width:size/unit,height:size/unit,x:Math.max(0,Math.min(scene.width-size,t.x+(oldSize-size)/2)),y:Math.max(0,Math.min(scene.height-size,t.y+oldHeight-size))};
 });
 if(changes.length)await scene.updateEmbeddedDocuments('Token',changes);
 return changes.length;
}
export function registerPresentation(){
 game.settings.register(MOD,'presentation',{scope:'world',config:false,type:Object,default:{...DEFAULT_PRESENTATION},onChange:()=>{fitPresentation();refreshFigures();Hooks.callAll('mrTronoPresentationChanged');}});
 // Extiende la clase configurada por el sistema, respetando su implementación y otros mundos.
 const Ruler=globalThis.CONFIG?.Token?.rulerClass;
 if(Ruler)CONFIG.Token.rulerClass=class TronoTokenRuler extends Ruler{get isVisible(){return owned(this.token.document.parent)&&presentationSettings().hideTrails?false:super.isVisible;}};
 Hooks.on('preMoveToken',(token,movement)=>{if(!owned(token.parent))return;const p=presentationSettings();if(p.lockRotation)movement.autoRotate=false;if(p.hideTrails)movement.showRuler=false;});
 Hooks.on('preCreateToken',(token)=>{if(!owned(token.parent))return;const p=presentationSettings();const scene=token.parent,unit=scene.grid.size||100,stage=p.depthScale?stageFor(scene):null;
  if(token._source.flags?.[MOD]?.placed){token.updateSource({lockRotation:p.lockRotation});return;}
  const nominal=Math.min(p.tokenPixels,scene.height,scene.width)/unit;
  const patch=stage?depthPatch(scene,{width:nominal,height:nominal,x:token.x,y:token.y},p.tokenPixels,stage):{width:nominal,height:nominal};
  token.updateSource({...patch,lockRotation:p.lockRotation});});
 // Al arrastrar una figura hacia el fondo se empequeñece; hacia el frente, crece (una sola actualización).
 Hooks.on('preUpdateToken',(token,changes)=>{
  const p=presentationSettings();const scene=token.parent;if(!p.depthScale||!owned(scene)||!game.user.isGM)return;
  if(changes.width!==undefined||changes.height!==undefined||(changes.x===undefined&&changes.y===undefined))return;
  if(token.actor?.getFlag?.(MOD,'source')!==MOD)return;const stage=stageFor(scene);if(!stage)return;
  Object.assign(changes,depthPatch(scene,token,p.tokenPixels,stage,{x:changes.x,y:changes.y}));});
 Hooks.once('ready',()=>loadStages());
 Hooks.on('canvasReady',()=>{fitPresentation();refreshFigures();});
 Hooks.on('canvasPan',()=>fitPresentation(false));
}
