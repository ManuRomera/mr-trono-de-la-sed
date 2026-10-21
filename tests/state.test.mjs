import test from 'node:test';
import assert from 'node:assert/strict';
import { MODULE_ID, escapeHTML, normalizeMemories, nativeStatuses, initialCampaign, normalizeCampaign, discardUpdates } from '../js/state.mjs';

test('escape dynamic values in HTML attributes and text', () => {
  assert.equal(escapeHTML(`<img src="x" onerror='alert(1)'>&`), '&lt;img src=&quot;x&quot; onerror=&#39;alert(1)&#39;&gt;&amp;');
});

test('memory records accept perceived narrative fields and discard secret/system fields', () => {
  const raw = { trueName:'Zahra', secrets:'GM only', statuses:[{tier:6}], entries:[{title:'A song', detail:'My mother', anchor:'Lute', condition:'recovered', tier:6, secret:'Never share'}] };
  const result = normalizeMemories(raw);
  assert.deepEqual(Object.keys(result).sort(), ['bonds','changes','entries','trueName']);
  assert.deepEqual(result.entries[0], {title:'A song',detail:'My mother',anchor:'Lute',condition:'recovered'});
  assert.equal(raw.entries[0].secret, 'Never share');
});

test('memory normalizer validates enum and bounds stored text and count', () => {
  const result = normalizeMemories({trueName:'n'.repeat(1000),entries:Array.from({length:100}, () => ({title:'t'.repeat(500),condition:'eraseTheme'}))});
  assert.equal(result.trueName.length,120);
  assert.equal(result.entries.length,60);
  assert.equal(result.entries[0].title.length,180);
  assert.equal(result.entries[0].condition,'established');
});

test('native statuses derive their current tier from markings, not a stale cached value', () => {
  const actor={system:{floatingTagsAndStatuses:[
    {name:'recuerdos-desvanecidos',isStatus:true,positive:false,value:6,markings:[false,true,false,false,false,false]},
    {name:'protegido',isStatus:true,positive:true,value:1,markings:[false,false,false,true,false,false]},
    {name:'historia',isStatus:false,value:3,markings:[false,false,true,false,false,false]}
  ]}};
  const snapshot=JSON.stringify(actor);
  assert.deepEqual(nativeStatuses(actor),[
    {name:'recuerdos-desvanecidos',tier:2,positive:false},
    {name:'protegido',tier:4,positive:true}
  ]);
  assert.equal(JSON.stringify(actor),snapshot);
  assert.deepEqual(nativeStatuses({}),[]);
});

test('initial campaign has six captives, an empty seventh vessel, and two intact seals', () => {
  const state=initialCampaign();
  assert.equal(state.vessels.length,7);
  assert.equal(state.vessels.filter(v=>v.state==='captive').length,6);
  assert.equal(state.vessels[6].state,'empty');
  assert.equal(state.meritSeal,'intact');assert.equal(state.priestSeal,'intact');
});

test('campaign validation preserves canonical victim names and validates ritual states', () => {
  const state=normalizeCampaign({heart:'delete-actor',meritSeal:'broken',vessels:[{name:'Replace Hori',state:'freed',notes:'saved'}],notes:'x'.repeat(13000)});
  assert.equal(state.heart,'protected');assert.equal(state.meritSeal,'broken');
  assert.equal(state.vessels[0].name,'Hori');assert.equal(state.vessels[0].state,'freed');assert.equal(state.vessels[0].notes,'saved');
  assert.equal(state.vessels[1].state,'captive');assert.equal(state.notes.length,12000);
});

test('additive import suppresses all updates while preserving create data', () => {
  const toCreate={Actor:[{_id:'new'}]};
  const toUpdate={Actor:[{_id:'existing',name:'edited'}],Scene:[{_id:'scene'}],JournalEntry:[]};
  assert.equal(discardUpdates(toUpdate),2);
  assert.deepEqual(toUpdate,{});
  assert.deepEqual(toCreate,{Actor:[{_id:'new'}]});
  assert.equal(MODULE_ID,'mr-trono-de-la-sed');
});
