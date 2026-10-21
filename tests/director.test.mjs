import test from 'node:test';import assert from 'node:assert/strict';
import {audioVolume,missingCast,splitCommand,dispatchDirector} from '../js/director.mjs';
test('reading mix reduces music and clamps invalid levels',()=>{assert.equal(audioVolume(.5,true),.14);assert.equal(audioVolume(3,false),1);assert.equal(audioVolume(-2,false),0);assert.equal(audioVolume('bad',false),.3);});
test('cast placement ignores actors already present but keeps missing characters',()=>{assert.deepEqual(missingCast([{actorId:'a'}],[{id:'a'},{id:'b'}]),[{id:'b'}]);});
test('journal action parser preserves scene and actor arguments',()=>{assert.deepEqual(splitCommand('token|pesaje~neb-sekhem'),{action:'token',arg:'pesaje~neb-sekhem'});assert.equal(splitCommand('invalid'),null);});
test('players cannot execute journal sound, scene, or actor actions',async()=>{globalThis.game={user:{isGM:false}};for(const x of ['music','effect','activate','actor','token','quiet','stop'])assert.equal(await dispatchDirector(x,'pesaje'),false);});
test('secondary Narrator cannot modify audio or place tokens',async()=>{let warned=0;globalThis.game={user:{id:'gm2',isGM:true},users:{activeGM:{id:'gm1'}},i18n:{localize:s=>s}};globalThis.ui={notifications:{warn(){warned++;}}};assert.equal(await dispatchDirector('music','pesaje'),false);assert.equal(await dispatchDirector('heroes','pesaje'),false);assert.equal(warned,2);});
