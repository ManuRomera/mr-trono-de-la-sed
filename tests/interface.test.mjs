/** Contract checks with a minimal Foundry adapter. These are not live Foundry tests. */
import test, {beforeEach} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {initialCampaign} from '../js/state.mjs';
import {createPrivateKey,encryptCampaign,decryptCampaign,makeCampaignBackup} from '../js/private-store.mjs';

const MOD='mr-trono-de-la-sed', PACK=`${MOD}.aventura`;
const hooks=new Map();
let menuClasses, settings, settingScopes, notifications, confirmation, packReads, imports, registryWrites, creations, tourEvents;
class ApplicationStub {
  constructor(options={}) {this.options=options;this.position={width:940,height:720};this.rendered=false;}
  async render() {this.rendered=true;tourEvents.push(['render',this.constructor.name]);return this;}
  bringToFront() {}
}
globalThis.Hooks={on:addHook,once:addHook};
function addHook(name,fn) {hooks.set(name,[...(hooks.get(name)??[]),fn]);}
class TourStub {
  static activeTour=null;
  constructor(config) {this.config=config;this.currentStep=config.steps[0];}
  static async fromJSON(path) {return new this(JSON.parse(await fs.readFile(new URL('../tours/'+path.split('/').at(-1),import.meta.url),'utf8')));}
  async reset() {this.currentStep=this.config.steps[0];tourEvents.push(['reset',this.id]);}
  async start() {TourStub.activeTour=this;await this._preStep();tourEvents.push(['start',this.id]);}
  async _preStep() {}
  async exit() {TourStub.activeTour=null;tourEvents.push(['exit',this.id]);}
}
globalThis.foundry={nue:{Tour:TourStub},applications:{api:{ApplicationV2:ApplicationStub,DialogV2:{confirm:async()=>{confirmation.calls++;return confirmation.accept;}}}}};
globalThis.CONST={DOCUMENT_OWNERSHIP_LEVELS:{NONE:0}};
globalThis.FormData=class {
  constructor(form) {this.values=form.values;}
  get(key) {return this.values[key]??null;}
};
const module=await import('../js/main.mjs');
function collection(contents=[]) {
  return {contents,get size(){return contents.length;},get:id=>contents.find(doc=>doc.id===id),find:predicate=>contents.find(predicate)};
}
function flagsDocument(id, name, flags={}, extra={}) {
  return {id,name,flags,getFlag(scope,key){return this.flags[scope]?.[key];},async setFlag(scope,key,value){this.flags[scope]??={};this.flags[scope][key]=value;},async update(changes){for(const [path,value]of Object.entries(changes)){const parts=path.split('.');let object=this;for(const part of parts.slice(0,-1)){object[part]??={};object=object[part];}const key=parts.at(-1);if(key.startsWith('-='))delete object[key.slice(2)];else object[key]=value;}return this;},...extra};
}
function hero(id, name, owner=true, source=MOD) {
  return flagsDocument(id,name,{[MOD]:{source,slug:id,memories:{trueName:name,entries:[{title:'My first memory',detail:'Original',anchor:'Ring',condition:'established'}]}}},{
    type:'litm-character',isOwner:owner,system:{floatingTagsAndStatuses:[]},
    testUserPermission(){return this.isOwner;},sheet:{render(){creations.push(['sheet',id]);}}
  });
}
function reset() {
  menuClasses={};settings=new Map();settingScopes={};notifications=[];confirmation={accept:true,calls:0};packReads=0;imports=0;registryWrites=[];creations=[];tourEvents=[];TourStub.activeTour=null;globalThis.document={querySelector:()=>({})};
  const record=flagsDocument('registry','Private register',{[MOD]:{registry:true,campaign:initialCampaign()}},{
    async setFlag(scope,key,value){registryWrites.push(value);this.flags[scope][key]=value;}
  });
  globalThis.ui={notifications:{info:value=>notifications.push(['info',value]),warn:value=>notifications.push(['warn',value]),error:value=>notifications.push(['error',value])}};
  globalThis.game={
    world:{id:'test-world'},user:{id:'gm',name:'Narrator',isGM:true},users:{activeGM:{id:'gm'}},
    actors:collection(),items:collection(),journal:collection([record]),scenes:collection(),playlists:collection(),macros:collection(),tables:collection(),cards:collection(),
    modules:new Map([[MOD,{}]]),system:{id:'mist-engine-fvtt'},
    i18n:{localize:key=>key,format:(key,data)=>key+JSON.stringify(data)},
    keybindings:{register(){}},
    settings:{register:(_scope,key,options)=>{settings.set(key,options.default);settingScopes[key]=options.scope;},get:(_scope,key)=>settings.get(key),set:async(_scope,key,value)=>{settings.set(key,value);return value;},registerMenu:(_scope,key,options)=>{menuClasses[key]=options.type;}},
    tours:Object.assign(new Map(),{register(namespace,id,tour){tour.id=id;tour.namespace=namespace;this.set(`${namespace}.${id}`,tour);}}),
    packs:new Map([[PACK,{getDocuments:async()=>{packReads++;return [adventure];}}]])
  };
  globalThis.JournalEntry={create:async(data)=>{const doc=flagsDocument('new-registry',data.name,data.flags,{ownership:data.ownership});game.journal.contents.push(doc);creations.push(data);return doc;}};
  for(const init of hooks.get('init')??[]) init();
}
const adventure={
  pack:PACK,
  prepareImport:async(options)=>{
    // Foundry v13 implementation requires options although online docs mark it optional.
    assert.deepEqual(options.importFields,[]);
    return {toCreate:{Actor:imports?[]:[{_id:'newHero',name:'New Hero'}]},toUpdate:{Actor:[{_id:'editedHero',name:'would overwrite'}]},documentCount:2};
  },
  async import() {
    const data=await this.prepareImport({importFields:[]});
    for(const callback of hooks.get('preImportAdventure')??[]) callback(this,{},data.toCreate,data.toUpdate);
    assert.deepEqual(data.toUpdate,{});
    for(const actor of data.toCreate.Actor) game.actors.contents.push(hero(actor._id,actor.name));
    for(const actor of data.toUpdate.Actor??[]) game.actors.get(actor._id).name=actor.name;
    imports++;
  }
};
async function readPrivateCampaign(document=game.journal.contents[0]) {
  const key=settings.get('privateKeys')?.[`${game.world.id}:${game.user.id}`];
  return decryptCampaign(document.getFlag(MOD,'privateCampaign'),key);
}
beforeEach(reset);

test('manual core import is additive for this Adventure and does not touch other modules', () => {
  const guard=hooks.get('preImportAdventure')[0];
  const creates={Actor:[{_id:'new'}]};const updates={Actor:[{_id:'edited'}],Scene:[{_id:'scene'}]};
  guard({compendium:{collection:PACK}}, {},creates,updates);
  assert.deepEqual(updates,{});assert.equal(creates.Actor.length,1);
  const unrelated={Actor:[{_id:'someoneElse'}]};
  guard({pack:'another.adventure'}, {},{},unrelated);
  assert.equal(unrelated.Actor.length,1);
});

test('import requires a GM and the active Narrator before reading compendium data', async () => {
  game.user.isGM=false;await module.importAdventure();assert.equal(packReads,0);assert.equal(confirmation.calls,0);
  game.user.isGM=true;game.users.activeGM={id:'otherGM'};await module.importAdventure();assert.equal(packReads,0);
  assert.equal(notifications.filter(([kind])=>kind==='warn').length,2);
});

test('declining import changes no documents, progress, or registry', async () => {
  confirmation.accept=false;const before=JSON.stringify(game.journal.contents[0].flags);
  await module.importAdventure();
  assert.equal(imports,0);assert.equal(game.actors.size,0);assert.equal(settings.get('imported'),false);
  assert.equal(registryWrites.length,0);assert.equal(JSON.stringify(game.journal.contents[0].flags),before);
});

test('accepted import creates additions, preserves edits and progress, and avoids duplicates', async () => {
  game.actors.contents.push(hero('editedHero','User edited name'));
  game.journal.contents[0].flags[MOD].campaign.vessels[0].state='freed';
  game.journal.contents[0].flags[MOD].campaign.nebNotes='User edited promise';
  await module.importAdventure();
  assert.equal(imports,1);assert.equal(game.actors.get('editedHero').name,'User edited name');
  assert.equal(game.actors.get('newHero').name,'New Hero');assert.equal(settings.get('imported'),true);
  const restored=await readPrivateCampaign();
  assert.equal(restored.vessels[0].state,'freed');
  assert.equal(restored.nebNotes,'User edited promise');
  assert.equal(game.journal.contents[0].getFlag(MOD,'campaign'),undefined);
  await module.importAdventure();assert.equal(imports,1);assert.equal(confirmation.calls,1);
});

test('import creates a private Narrator register, not public actor flags or settings', async () => {
  game.journal.contents.length=0;
  const hori=hero('hori','Hori');hori.system.biography='<p>Hermano de Panehsy.</p><script>doNotCopy()</script>';hori.system.shortDescription='El ausente';
  const neb=hero('neb','Neb-Sekhem');neb.system.biography='<p>Un príncipe prisionero.</p>';neb.system.secrets=[{name:'Corazón',description:'Está sellado.'}];
  game.actors.contents.push(hori,neb);
  game.journal.contents.push(flagsDocument('session2','II · La corte',{[MOD]:{source:MOD,slug:'sesion2'}},{pages:{contents:[{name:'Tentación de Zahra: un registro sin culpa',text:{content:'<p>Promete borrar su culpa.</p>'}}]}}));
  await module.importAdventure();
  const registry=game.journal.contents.find(doc=>doc.getFlag(MOD,'registry'));
  assert.ok(registry);assert.equal(registry.ownership.default,0);
  assert.equal(settings.get('registryId'),registry.id);
  const privateState=await readPrivateCampaign(registry);
  assert.match(privateState.vessels[0].notes,/Hermano de Panehsy/);
  assert.doesNotMatch(privateState.vessels[0].notes,/<p>|doNotCopy/);
  assert.match(privateState.nebNotes,/Corazón: Está sellado/);
  assert.match(privateState.nebNotes,/Tentación de Zahra/);
  assert.match(privateState.nebNotes,/Promete borrar su culpa/);
  assert.equal(registry.getFlag(MOD,'campaign'),undefined);
  assert.doesNotMatch(JSON.stringify(registry.flags),/Hermano|Corazón|culpa/);
  assert.equal(settings.has('campaign'),false);
  assert.equal(game.actors.get('newHero').getFlag(MOD,'campaign'),undefined);
});

test('private Narrator book refuses rendering and actions to a player', async () => {
  const book=new menuClasses.gmBook();game.user.isGM=false;
  assert.equal(book._canRender(),false);assert.equal(await book.content(),'');
  let shown=false;game.journal.contents.push(flagsDocument('handout','Visible',{[MOD]:{audience:'players'}},{show:async()=>{shown=true;}}));
  await book.action('show',{dataset:{id:'handout'}});
  assert.equal(shown,false);assert.equal(registryWrites.length,0);
});

test('memory selection excludes unowned Heroes and unrelated module documents', async () => {
  game.user.isGM=false;
  game.actors.contents.push(hero('mine','<img src=x onerror=alert(1)>'),hero('other','Other secret',false),hero('foreign','Foreign source',true,'another-module'));
  game.actors.contents.push(flagsDocument('foreignSlug','Different namespace',{other:{slug:'foreignSlug'}},{type:'litm-character',isOwner:true}));
  const book=new menuClasses.memories();const html=await book.content();
  assert.ok(html.includes('&lt;img src=x onerror=alert(1)&gt;'));
  assert.ok(!html.includes('<img src=x'));assert.ok(!html.includes('Other secret'));
  assert.ok(!html.includes('Foreign source'));assert.ok(!html.includes('Different namespace'));
});

test('lost Actor ownership cannot redirect an unsaved form to another owned Hero', async () => {
  game.user.isGM=false;
  const first=hero('first','Zahra'),second=hero('second','Seneb');game.actors.contents.push(first,second);
  const book=new menuClasses.memories();book.actorId='first';book.dirty=true;
  first.isOwner=false;
  await assert.rejects(book.action('saveMemories',{}),/OwnerOnly/);
  assert.equal(second.getFlag(MOD,'memories').entries[0].detail,'Original');
});

test('saving memories changes narrative flags only, never native tags, statuses, or themes', async () => {
  game.user.isGM=false;const actor=hero('mine','Zahra');
  actor.system={floatingTagsAndStatuses:[{name:'olvido',isStatus:true,markings:[false,true,false,false,false,false]}],themes:['nativeTheme']};
  game.actors.contents.push(actor);const before=JSON.stringify(actor.system);
  const book=new menuClasses.memories();book.actorId=actor.id;
  book.element={querySelector:()=>({values:{trueName:'Zahra',bonds:'Seneb',changes:'We remember',title0:'A song',detail0:'Recovered at the banquet',anchor0:'Lute',condition0:'recovered'}})};
  await book.action('saveMemories',{});
  assert.equal(actor.getFlag(MOD,'memories').entries[0].condition,'recovered');
  assert.equal(actor.getFlag(MOD,'memories').bonds,'Seneb');assert.equal(JSON.stringify(actor.system),before);
});

test('only explicit player handouts can be broadcast, while GM journals remain private', async () => {
  const shown=[];const make=(id,audience)=>flagsDocument(id,id,{[MOD]:{source:MOD,audience}},{show:async(force)=>shown.push([id,force])});
  game.journal.contents.push(make('gm-secret','gm'),make('player-letter','players'));
  const book=new menuClasses.gmBook();
  await book.action('show',{dataset:{id:'gm-secret'}});assert.deepEqual(shown,[]);
  await book.action('show',{dataset:{id:'player-letter'}});assert.deepEqual(shown,[['player-letter',true]]);
});

test('first-run detection ignores only native scene-data Items alongside the Foundry welcome Scene', () => {
  game.journal.contents.length=0;
  game.items.contents.push({type:'scene-data',name:'Scene Data: Foundry'});
  game.scenes.contents.push({id:'NUEDEFAULTSCENE0',background:{src:'nue/defaultscene/fvtt-background.webp'},tokens:{size:0}});
  assert.equal(module.emptyWorld(),true);
  game.items.contents.push({type:'backpack'});assert.equal(module.emptyWorld(),false);
  game.items.contents.pop();game.actors.contents.push(hero('mine','Zahra'));assert.equal(module.emptyWorld(),false);
  game.actors.contents.pop();game.scenes.contents[0].tokens.size=1;assert.equal(module.emptyWorld(),false);
  game.scenes.contents[0].tokens.size=0;game.scenes.contents[0].id='user-created-scene';assert.equal(module.emptyWorld(),false);
});

test('fresh world with native helper offers import only once and keeps acceptance pending', async () => {
  game.journal.contents.length=0;game.items.contents.push({type:'scene-data'});
  game.scenes.contents.push({id:'NUEDEFAULTSCENE0',background:{src:'nue/defaultscene/fvtt-background.webp'},tokens:{size:0}});
  confirmation.accept=false;
  for(const callback of hooks.get('ready')) await callback();
  assert.equal(confirmation.calls,1);assert.equal(imports,0);assert.equal(settings.get('offered'),true);
  for(const callback of hooks.get('ready')) await callback();
  assert.equal(confirmation.calls,1);
});

test('native tours register, open the corresponding book first, and leave campaign data unchanged', async () => {
  const before=JSON.stringify(game.journal.contents[0].flags);
  await module.startTutorial('narrator');
  const tour=game.tours.get(`${MOD}.narrator`);
  assert.ok(tour instanceof TourStub);assert.equal(tour.config.restricted,true);
  assert.equal(tour.config.steps.length,7);
  const startIndex=tourEvents.findIndex(event=>event[0]==='start');
  assert.ok(tourEvents.slice(0,startIndex).some(event=>event[0]==='render'&&event[1]==='BookGM'));
  assert.equal(tour.currentStep.selector,'#mr-trono-gm .mr-book');
  assert.equal(JSON.stringify(game.journal.contents[0].flags),before);
});

test('player can start player tour but cannot start private Narrator tour', async () => {
  game.user.isGM=false;
  await module.startTutorial('narrator');assert.equal(game.tours.size,0);
  await module.startTutorial('players');
  assert.ok(game.tours.has(`${MOD}.players`));
  assert.equal(game.tours.get(`${MOD}.players`).config.restricted,false);
  assert.ok(tourEvents.some(event=>event[0]==='render'&&event[1]==='BookMemories'));
});

test('tour steps without an available element fall back centrally instead of failing', async () => {
  game.user.isGM=false;document.querySelector=()=>null;
  await module.startTutorial('players');
  const tour=game.tours.get(`${MOD}.players`);
  assert.equal(tour.currentStep.selector,'');
  document.querySelector=()=>({});await tour._preStep();
  assert.equal(tour.currentStep.selector,'#mr-trono-memories .mr-book');
});

test('legacy private notes migrate atomically to authenticated ciphertext with a client-only key', async () => {
  const record=game.journal.contents[0];record.flags[MOD].campaign.notes='PRIVATE_CANARY_NO_NETWORK';
  const book=new menuClasses.gmBook();await book.content();
  assert.equal(settingScopes.privateKeys,'client');
  assert.equal(record.getFlag(MOD,'campaign'),undefined);
  assert.deepEqual(Object.keys(record.getFlag(MOD,'privateCampaign')).sort(),['ciphertext','iv','v']);
  assert.doesNotMatch(JSON.stringify(record.flags),/PRIVATE_CANARY_NO_NETWORK/);
  assert.equal((await readPrivateCampaign(record)).notes,'PRIVATE_CANARY_NO_NETWORK');
});

test('missing local key locks an existing encrypted campaign without generating or resetting anything', async () => {
  const record=game.journal.contents[0];const state=initialCampaign();state.notes='UNREADABLE_WITHOUT_KEY';
  delete record.flags[MOD].campaign;
  record.flags[MOD].privateCampaign=await encryptCampaign(state,await createPrivateKey());
  const before=JSON.stringify(record.flags);const book=new menuClasses.gmBook();const html=await book.content();
  assert.ok(html.includes('MRTRONO.PrivateLocked'));
  assert.ok(!html.includes('UNREADABLE_WITHOUT_KEY'));
  assert.deepEqual(settings.get('privateKeys'),{});assert.equal(JSON.stringify(record.flags),before);
});

test('local backup recovery creates ciphertext and preserves unrelated world documents', async () => {
  const record=game.journal.contents[0];const state=initialCampaign();state.nebNotes='RECOVERED_LOCAL_PROMISE';
  const backup=makeCampaignBackup(state,{worldId:'old-world',userId:'old-gm'});
  const actor=hero('unchanged','Zahra');game.actors.contents.push(actor);const actorBefore=JSON.stringify(actor);
  await module.importPrivateBackup(JSON.stringify(backup));
  assert.equal(record.getFlag(MOD,'campaign'),undefined);
  assert.equal((await readPrivateCampaign(record)).nebNotes,'RECOVERED_LOCAL_PROMISE');
  assert.doesNotMatch(JSON.stringify(record.flags),/RECOVERED_LOCAL_PROMISE/);
  assert.equal(JSON.stringify(actor),actorBefore);
});

test('players cannot restore private backups or initialize private encryption keys', async () => {
  game.user.isGM=false;
  await assert.rejects(module.importPrivateBackup(JSON.stringify(makeCampaignBackup(initialCampaign()))),/ActiveGMOnly/);
  assert.deepEqual(settings.get('privateKeys'),{});
});
