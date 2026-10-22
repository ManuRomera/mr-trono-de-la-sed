import test from 'node:test';import assert from 'node:assert/strict';
import {HITOS,hitosState,hitosProgress,lampsValue,lampsAfterClick,lampsStage,clampPill,panelSide} from '../js/hitos.mjs';
import {ambientFor,AMBIENTS} from '../js/director.mjs';
test('milestones normalise unknown or missing values and count progress',()=>{
 assert.equal(hitosState(undefined).funeral,false);
 assert.equal(Object.keys(hitosState({x:true})).length,HITOS.length);
 assert.deepEqual(hitosProgress({funeral:true,pozo:true,nope:true}),{done:2,total:HITOS.length});
});
test('ambient presets are ordered from bright to dark and unknown keys are rejected',()=>{
 assert.ok(AMBIENTS.light.dark<AMBIENTS.dim.dark&&AMBIENTS.dim.dark<AMBIENTS.dark.dark);
 assert.ok(AMBIENTS.light.level>AMBIENTS.dark.level);
 assert.equal(ambientFor('nope'),null);assert.equal(ambientFor('dim').dark,.38);
});
test('the seven lamps clamp, toggle from the clicked lamp and map to court stages',()=>{
 assert.equal(lampsValue(undefined),7);assert.equal(lampsValue(-3),0);assert.equal(lampsValue(99),7);
 assert.equal(lampsAfterClick(7,3),3);assert.equal(lampsAfterClick(3,5),6);assert.equal(lampsAfterClick(1,0),0);
 assert.deepEqual([7,5,4,3,2,1,0].map(lampsStage),['7','7','4','3','2','1','0']);
});
test('badge position is clamped to the viewport and the panel opens toward the free side',()=>{
 assert.deepEqual(clampPill({x:-5,y:-5},[120,34],[1600,900]),{x:0,y:0});
 assert.deepEqual(clampPill({x:9999,y:9999},[120,34],[1600,900]),{x:1480,y:866});
 assert.equal(panelSide({x:20,y:800},[1600,900]),'above');assert.equal(panelSide({x:20,y:100},[1600,900]),'below');
});
