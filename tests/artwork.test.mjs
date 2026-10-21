import test from 'node:test';
import assert from 'node:assert/strict';
import {artworkPatch} from '../js/art-upgrade.mjs';
const MOD='mr-trono-de-la-sed';
const actor=(extra={})=>({_id:'test',type:'litm-npc',name:'Neb-Sekhem',img:'icons/svg/mystery-man.svg',flags:{[MOD]:{source:MOD}},prototypeToken:{texture:{src:'icons/svg/mystery-man.svg'}},...extra});
test('artwork upgrade fills existing module NPC art, including full body token',()=>{
 const p=artworkPatch(actor());assert.equal(p.img,`modules/${MOD}/assets/npc/neb-sekhem-portrait.webp`);assert.equal(p['prototypeToken.texture.src'],`modules/${MOD}/assets/npc/neb-sekhem-token.webp`);assert.deepEqual(Object.keys(p),['_id','img','prototypeToken.texture.src']);
});
test('artwork upgrade preserves custom portrait and custom token independently',()=>{
 let p=artworkPatch(actor({img:'worlds/mygame/my-portrait.webp'}));assert.equal(p.img,undefined);assert.ok(p['prototypeToken.texture.src']);
 p=artworkPatch(actor({prototypeToken:{texture:{src:'worlds/mygame/my-token.webp'}}}));assert.ok(p.img);assert.equal(p['prototypeToken.texture.src'],undefined);
 assert.equal(artworkPatch(actor({img:'custom/a.png',prototypeToken:{texture:{src:'custom/b.png'}}})),null);
});
test('artwork upgrade never touches unrelated actors or another module',()=>{
 assert.equal(artworkPatch(actor({flags:{}})),null);assert.equal(artworkPatch(actor({name:'Someone else'})),null);assert.equal(artworkPatch(actor({flags:{[MOD]:{source:'another'}}})),null);
});
