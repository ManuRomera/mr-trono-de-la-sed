/** Actualiza exclusivamente campos artísticos propios; respeta imágenes personalizadas. */
const MOD='mr-trono-de-la-sed';
const prefix=`modules/${MOD}/assets/`;
const people=['Merit','Khety','Tia','Panehsy','Nefru','Serekh','Neb-Sekhem','Hori','Paser','Tamerit','Kasa','Beset','Dedi','Henut'];
export function artworkPatch(actor) {
  if(actor.type!=='litm-npc' || actor.flags?.[MOD]?.source!==MOD || !people.includes(actor.name)) return null;
  const slug=actor.name.toLowerCase();
  const owned=value=>!value || value.startsWith('icons/') || value.startsWith(`modules/${MOD}/`);
  const patch={_id:actor._id??actor.id};
  if(owned(actor.img)) patch.img=`${prefix}npc/${slug}-portrait.webp`;
  const token=actor.prototypeToken?.texture?.src;
  if(owned(token)) patch['prototypeToken.texture.src']=`${prefix}npc/${slug}-token.webp`;
  return Object.keys(patch).length>1 ? patch : null;
}
export async function upgradeArtwork() {
  if(!game.user.isGM || (game.users.activeGM && game.users.activeGM.id!==game.user.id)) return;
  const patches=game.actors.contents.map(actor=>artworkPatch(actor.toObject?.() ?? actor)).filter(Boolean).filter(patch=>{
    const a=game.actors.get(patch._id);
    return (patch.img && a.img!==patch.img) || (patch['prototypeToken.texture.src'] && a.prototypeToken.texture.src!==patch['prototypeToken.texture.src']);
  });
  if(patches.length) await Actor.updateDocuments(patches);
  // Los tokens ya colocados también conservan imágenes personales.
  for(const scene of game.scenes.contents) {
    const updates=[];
    for(const token of (scene.tokens?.contents ?? [])) {
      const actor=game.actors.get(token.actorId);if(!actor)continue;
      const p=artworkPatch(actor.toObject?.() ?? actor);const old=token.texture.src;
      if(p?.['prototypeToken.texture.src'] && (!old || old.startsWith('icons/') || old.startsWith(`modules/${MOD}/`)) && old!==p['prototypeToken.texture.src']) updates.push({_id:token.id,'texture.src':p['prototypeToken.texture.src']});
    }
    if(updates.length) await scene.updateEmbeddedDocuments('Token',updates);
  }
}
