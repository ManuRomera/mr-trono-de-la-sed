/** Encuadre panorámico y figuras: ajustes limitados a las escenas de esta aventura. */
const MOD='mr-trono-de-la-sed';
const owned=s=>s?.getFlag?.(MOD,'source')===MOD;
const activeGM=()=>game.user.isGM&&(!game.users.activeGM||game.users.activeGM.id===game.user.id);
export const DEFAULT_PRESENTATION=Object.freeze({tokenPixels:360,lockRotation:true,hideTrails:true,cover:true});
export function presentationOptions(value={}){
 const pixels=Number(value.tokenPixels);
 return {tokenPixels:Math.round(Math.min(900,Math.max(60,Number.isFinite(pixels)?pixels:360))),lockRotation:value.lockRotation!==false,hideTrails:value.hideTrails!==false,cover:value.cover!==false};
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
 const pixels=presentationSettings().tokenPixels,unit=scene.grid.size||100;
 const changes=scene.tokens.contents.filter(t=>!ids||ids.has(t.id)).map(t=>{
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
 Hooks.on('preCreateToken',(token)=>{if(!owned(token.parent))return;const p=presentationSettings();const size=Math.min(p.tokenPixels,token.parent.height,token.parent.width)/(token.parent.grid.size||100);token.updateSource({width:size,height:size,lockRotation:p.lockRotation});});
 Hooks.on('canvasReady',()=>{fitPresentation();refreshFigures();});
 Hooks.on('canvasPan',()=>fitPresentation(false));
}
