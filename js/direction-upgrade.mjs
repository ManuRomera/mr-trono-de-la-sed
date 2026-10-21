/** Completa enlaces nuevos de dirección sin reemplazar contenidos personalizados. */
const MOD='mr-trono-de-la-sed';
export function directionPatch(existing,target){
 if(existing.flags?.[MOD]?.source!==MOD||!target)return null;
 const p={_id:existing._id??existing.id};
 for(const key of ['journal','journalEntryPage','playlist','playlistSound']){
  const old=existing[key];const wanted=target[key];
  if(!old&&wanted&&!(key==='journalEntryPage'&&existing.journal&&existing.journal!==target.journal)&&!(key==='playlistSound'&&existing.playlist&&existing.playlist!==target.playlist))p[key]=wanted;
 }
 if(!existing.flags?.[MOD]?.direction&&target.flags?.[MOD]?.direction)p[`flags.${MOD}.direction`]=target.flags[MOD].direction;
 return Object.keys(p).length>1?p:null;
}
export async function upgradeDirection(){
 if(!game.user.isGM||(game.users.activeGM&&game.users.activeGM.id!==game.user.id)||!game.scenes.contents.some(s=>s.getFlag?.(MOD,'source')===MOD))return;
 const pack=game.packs.get(MOD+'.aventura');if(!pack)return;
 const adv=(await pack.getDocuments())[0];if(!adv)return;
 const targets=new Map(adv.toObject().scenes.map(s=>[s._id,s]));const patches=[];
 for(const s of game.scenes.contents){const p=directionPatch(s.toObject(),targets.get(s.id));if(!p)continue;
  // Los destinos deben estar importados antes de enlazarlos; no crear referencias huérfanas.
  if(p.journal&&!game.journal.has(p.journal))delete p.journal;
  if(p.journalEntryPage&&!game.journal.has(targets.get(s.id).journal))delete p.journalEntryPage;
  if(p.playlist&&!game.playlists.has(p.playlist))delete p.playlist;
  if(p.playlistSound&&!game.playlists.has(targets.get(s.id).playlist))delete p.playlistSound;
  if(Object.keys(p).length>1)patches.push(p);
 }
 if(patches.length)await Scene.updateDocuments(patches);
}
