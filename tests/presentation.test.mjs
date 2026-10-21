import test from 'node:test';import assert from 'node:assert/strict';
import {coverPosition,figureLayout,presentationOptions,figureSize,VISIBLE,stageLayout,depthPatch,FOOT} from '../js/presentation.mjs';
import {sceneFormatPatch,textMatches} from '../js/editorial-upgrade.mjs';
const MOD='mr-trono-de-la-sed';
test('cover fills 16:9, 16:10, 4:3, portrait and ultrawide viewports without stretching or gray edges',()=>{
 for(const screen of [[1920,1080],[1600,1000],[1600,1100],[1440,1080],[3440,1440],[1080,1920],[3840,2160]]){
  const rect={x:0,y:0,width:1920,height:1080};
  for(const center of [true,false]){
   const p=coverPosition(rect,screen,{x:-999,y:9999,scale:.1},center);
   assert.ok(rect.width*p.scale>=screen[0]-.00001);assert.ok(rect.height*p.scale>=screen[1]-.00001);
   assert.ok(p.x-screen[0]/(2*p.scale)>=-.00001);assert.ok(p.y-screen[1]/(2*p.scale)>=-.00001);
   assert.ok(p.x+screen[0]/(2*p.scale)<=rect.width+.00001);assert.ok(p.y+screen[1]/(2*p.scale)<=rect.height+.00001);
  }
 }
});
test('figure placement uses configured pixels and stays within the current cropped viewport',()=>{
 const scene={width:1920,height:1080,grid:{size:100}},bounds={x:240,y:0,width:1440,height:1080};
 for(const size of [240,360,480])for(const token of figureLayout(scene,5,0,size,bounds)){
  assert.equal(token.width*100,size);assert.equal(token.height*100,size);
  assert.ok(token.x>=240&&token.x+size<=1680);assert.ok(token.y>=0&&token.y+size<=1080);
 }
 assert.equal(presentationOptions({tokenPixels:'bad'}).tokenPixels,360);
 assert.equal(presentationOptions({tokenPixels:-10}).tokenPixels,60);
});
test('edition migration retains identities, personal token data and transforms edited walls',()=>{
 const old={_id:'scene',width:1024,height:1536,padding:0,background:{src:'own.webp'},grid:{size:100},flags:{[MOD]:{source:MOD,slug:'portrait'}},tokens:[{_id:'token',actorId:'a',x:800,y:1300,width:1.5,height:1.5,texture:{src:'personal.webp'},flags:{personal:'keep'}}],walls:[{_id:'wall',c:[0,0,1024,1536],door:1}]};
 const baseline={...old,walls:[]},target={width:1920,height:1080,background:{src:'own.webp'}};
 const p=sceneFormatPatch(old,target,baseline);
 assert.equal(p.tokens[0]._id,'token');assert.equal(p.tokens[0].texture.src,'personal.webp');assert.equal(p.tokens[0].flags.personal,'keep');
 assert.equal(p.walls[0].door,1);assert.deepEqual(p.walls[0].c,[0,0,1920,1080]);
 assert.equal(sceneFormatPatch({...old,background:{src:'custom.webp'}},target,baseline),null);
 assert.equal(sceneFormatPatch({...old,width:2000},target,baseline),null);
 assert.equal(sceneFormatPatch({...old,flags:{[MOD]:{source:MOD,presentationEdition:'1.1.0'}}},target,baseline),null);
});
test('safe text upgrade matches only the untouched source',async()=>{
 const hash='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad';
 assert.equal(await textMatches('abc',hash),true);assert.equal(await textMatches('abc - my notes',hash),false);assert.equal(await textMatches('abc',undefined),false);
});
test('one-pixel dimensions from earlier art exports update while deliberate resizing remains personal',()=>{
 const old={_id:'s',width:1672,height:940,background:{src:'scene.webp'},grid:{size:100},tokens:[],flags:{[MOD]:{source:MOD,slug:'muhar'}}};
 const base={width:1672,height:941,background:{src:'scene.webp'}},target={width:1920,height:1080,background:{src:'scene.webp'}};
 assert.equal(sceneFormatPatch(old,target,base).height,1080);
 assert.equal(sceneFormatPatch({...old,width:1680},target,base),null);
});
test('the cast stands on a shared foreground baseline instead of stacking figures in the air',()=>{
 const positions=figureLayout({width:1920,height:1080,grid:{size:100}},5,0,480,{x:240,y:0,width:1440,height:1080});
 assert.equal(new Set(positions.map(t=>t.y+t.height*100)).size,1);
 assert.ok(positions.every((t,i)=>i===0||t.x>positions[i-1].x));
});

test('figure height follows perspective: head on the horizon, taller toward the camera',()=>{
 const stage={eye:.5,anchors:[]};
 const f=y=>figureSize(stage,y*1000,1000,360);
 assert.ok(f(.6)<f(.8)&&f(.8)<f(.95));
 assert.ok(Math.abs(f(.95)-(.45*1000/VISIBLE))<1);
 assert.equal(figureSize(stage,.3*1000,1000,360),60);                         // por encima del horizonte: mínimo
 assert.ok(Math.abs(figureSize(stage,700,1000,720)-2*figureSize(stage,700,1000,360))<1); // el ajuste global escala todo
});
test('stage layout puts feet on anchors and sizes each figure by its own depth',()=>{
 const scene={width:1920,height:1080,grid:{size:100}};
 const stage={eye:.5,anchors:[[.5,.65],[.3,.95],[.8,.8]]};
 const t=stageLayout(scene,3,0,360,stage);
 const feet=t.map(k=>k.y+k.height*100*(1-FOOT));
 assert.ok(Math.abs(feet[0]-.65*1080)<1&&Math.abs(feet[1]-.95*1080)<1);
 assert.ok(t[0].width<t[2].width&&t[2].width<t[1].width);
 for(const k of t){assert.ok(k.x>=0&&k.x+k.width*100<=1920&&k.y>=0&&k.y+k.height*100<=1080);}
 assert.equal(stageLayout(scene,7,0,360,stage).length,7);
});
test('depth patch keeps the centre and the foot line when a figure moves',()=>{
 const scene={width:1920,height:1080,grid:{size:100}},stage={eye:.5};
 const token={x:500,y:600,width:3.6,height:3.6};
 const back=depthPatch(scene,token,360,stage,{x:700,y:300}),front=depthPatch(scene,token,360,stage,{x:700,y:700});
 assert.ok(back.width<front.width);                     // más al fondo, más pequeño
 for(const [p,y] of [[back,300],[front,700]]){
  assert.ok(Math.abs((p.x+p.width*50)-(700+180))<.01);   // centro horizontal intacto
  assert.ok(Math.abs((p.y+p.height*100*(1-FOOT))-(y+360*(1-FOOT)))<.01); // pies en el mismo sitio
 }
});
