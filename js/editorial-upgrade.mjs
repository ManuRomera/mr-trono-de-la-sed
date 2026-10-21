/** Revisa la edición original de v1; los textos modificados por la mesa se conservan. */
const MOD='mr-trono-de-la-sed';
const owned=d=>d?.flags?.[MOD]?.source===MOD;
export async function textMatches(value,hash){
 if(typeof value!=='string'||!hash)return false;
 const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value));
 return [...new Uint8Array(bytes)].map(n=>n.toString(16).padStart(2,'0')).join('')===hash;
}
export function sceneFormatPatch(existing,target,baseline){
 if(!owned(existing)||!target||!baseline)return null;
 if(existing.flags[MOD].presentationEdition==='1.1.0')return null;
 // Una ilustración o dimensiones personales indican una composición de la mesa.
 if(existing.background?.src!==baseline.background?.src||Math.abs(existing.width-baseline.width)>1||Math.abs(existing.height-baseline.height)>1)return null;
 const p={_id:existing._id,width:target.width,height:target.height,padding:0,'background.src':target.background.src,[`flags.${MOD}.presentationEdition`]:'1.1.0'};
 const sx=target.width/existing.width,sy=target.height/existing.height;
 // En los planos se mantiene la escala uniforme y se añade piedra a ambos lados.
 const map=existing.flags[MOD].slug==='corte'||existing.flags[MOD].slug?.startsWith('map-');
 const scale=map?Math.min(sx,sy):null;const dx=map?(target.width-existing.width*scale)/2:0,dy=map?(target.height-existing.height*scale)/2:0;
 const point=(x,y)=>[Math.round(dx+x*(scale??sx)),Math.round(dy+y*(scale??sy))];
 p.grid={...existing.grid,size:Math.max(50,Math.round((existing.grid?.size||100)*(scale??Math.min(sx,sy))))};
 p.tokens=(existing.tokens??[]).map(t=>{const [x,y]=point(t.x,t.y);const oldUnit=existing.grid?.size||100,unit=p.grid.size;const ratio=scale??Math.min(sx,sy);const width=t.width*oldUnit*ratio/unit,height=t.height*oldUnit*ratio/unit;return {...t,x:Math.max(0,Math.min(target.width-width*unit,x)),y:Math.max(0,Math.min(target.height-height*unit,y)),width,height,lockRotation:true};});
 for(const key of ['walls','notes','lights','sounds','tiles','drawings','templates'])if(existing[key]?.length)p[key]=existing[key].map(d=>{
  const out={...d};if(Array.isArray(d.c))out.c=d.c.map((v,i)=>Math.round((i%2?dy:dx)+v*(scale??(i%2?sy:sx))));
  if(Number.isFinite(d.x)&&Number.isFinite(d.y))[out.x,out.y]=point(d.x,d.y);
  if(key==='tiles'){out.width=d.width*(scale??sx);out.height=d.height*(scale??sy);}
  if(key==='drawings'&&d.shape)out.shape={...d.shape,width:d.shape.width*(scale??sx),height:d.shape.height*(scale??sy),points:d.shape.points?.map((v,i)=>v*(scale??(i%2?sy:sx)))};
  return out;
 });
 if(JSON.stringify((existing.walls??[]).map(w=>w.c))===JSON.stringify(baseline.walls??[])&&target.walls?.length)p.walls=target.walls;
 return p;
}
export async function upgradeEditorial(){
 if(!game.user.isGM||(game.users.activeGM&&game.users.activeGM.id!==game.user.id)||!game.scenes.contents.some(s=>s.getFlag(MOD,'source')===MOD))return;
 const response=await fetch(`modules/${MOD}/content/upgrade-v1.json`);if(!response.ok)throw new Error('Falta la referencia de actualización editorial');
 const baseline=await response.json();const pack=game.packs.get(MOD+'.aventura');const adv=(await pack?.getDocuments())?.[0]?.toObject();if(!adv)return;
 const actors=[];
 for(const target of adv.actors){const a=game.actors.get(target._id);if(!a||!owned(a.toObject()))continue;
  if(a.system.biography!==target.system.biography&&await textMatches(a.system.biography,baseline.actors[a.id]))actors.push({_id:a.id,'system.biography':target.system.biography});
 }
 if(actors.length)await Actor.updateDocuments(actors);
 for(const target of adv.journal){const journal=game.journal.get(target._id);if(!journal)continue;if(!owned(journal.toObject()))continue;
  const changes=[],missing=[];
  for(const page of target.pages){const old=journal.pages.get(page._id);if(!old){missing.push(page);continue;}
   if(old.text?.content!==page.text?.content&&(await textMatches(old.text?.content,baseline.pages[old.id])||await textMatches(old.text?.content,baseline.previewPages?.[old.id])))changes.push({_id:old.id,name:page.name,'text.content':page.text.content});
  }
  if(changes.length)await journal.updateEmbeddedDocuments('JournalEntryPage',changes);
  if(missing.length)await journal.createEmbeddedDocuments('JournalEntryPage',missing,{keepId:true});
 }
 // Los capítulos reorganizados tienen IDs nuevos: las anotaciones de la edición anterior siguen accesibles.
 const additions=adv.journal.filter(j=>!game.journal.has(j._id)&&!(baseline.journalIds??[]).includes(j._id));
 const folderIds=new Set(additions.map(j=>j.folder).filter(Boolean));
 const folders=(adv.folders??[]).filter(f=>folderIds.has(f._id)&&!game.folders.has(f._id));
 if(folders.length)await Folder.createDocuments(folders,{keepId:true});
 if(additions.length)await JournalEntry.createDocuments(additions,{keepId:true});
 const legacy=(baseline.chapterIds??[]).map(id=>game.journal.get(id)).filter(j=>j&&owned(j.toObject())&&!j.getFlag(MOD,'editorialLegacy'));
 if(legacy.length)await JournalEntry.updateDocuments(legacy.map(j=>({_id:j.id,[`flags.${MOD}.editorialLegacy`]:true})));
 const targets=new Map(adv.scenes.map(s=>[s._id,s]));const patches=[];
 for(const scene of game.scenes){const patch=sceneFormatPatch(scene.toObject(),targets.get(scene.id),baseline.scenes[scene.id]);if(patch)patches.push(patch);}
 if(patches.length)await Scene.updateDocuments(patches,{animate:false});
}
