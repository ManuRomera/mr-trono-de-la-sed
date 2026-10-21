import test from 'node:test';import assert from 'node:assert/strict';
import {HITOS,hitosState,hitosProgress} from '../js/hitos.mjs';
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
