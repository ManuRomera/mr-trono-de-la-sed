/** MR · El Trono de la Sed. Narrative tools around the official Mist Engine. */
import { MODULE_ID as MOD, escapeHTML as esc, normalizeMemories, nativeStatuses,
  initialCampaign, normalizeCampaign, discardUpdates } from './state.mjs';
import {createPrivateKey, encryptCampaign, decryptCampaign, makeCampaignBackup, parseCampaignBackup} from './private-store.mjs';

import {registerPresentation} from './presentation.mjs';
import {upgradeArtwork} from './art-upgrade.mjs';
import {upgradeEditorial} from './editorial-upgrade.mjs';
import {upgradeDirection} from './direction-upgrade.mjs';
import {registerDirector,setupDirector,openSceneGuide,dispatchDirector} from './director.mjs';

const PACK = `${MOD}.aventura`;
const { ApplicationV2, DialogV2 } = foundry.applications.api;
const books = new Set();
let gmBook, memoryBook, importing = false;
let campaignQueue = Promise.resolve();
let campaignCache = null, campaignCacheId = '', campaignLocked = false;
let campaignVaultFingerprint = '';
let pendingVaultLoad = null;
const t = key => game.i18n.localize(`MRTRONO.${key}`);
const fmt = (key, data) => game.i18n.format(`MRTRONO.${key}`, data);
const own = actor => Boolean(actor && (game.user.isGM || actor.isOwner));
const belonging = doc => {
  const source = doc?.getFlag?.(MOD, 'source');
  if (source !== undefined && source !== null) return source === MOD;
  return Boolean(doc?.getFlag?.(MOD, 'slug') || doc?.getFlag?.(MOD, 'key'));
};
const docs = collection => (game[collection]?.contents ?? []).filter(doc=>belonging(doc)&&!doc.getFlag?.(MOD,'editorialLegacy'));
const heroActors = () => docs('actors').filter(actor => actor.type === 'litm-character' || actor.type === 'character');
const activeNarrator = () => game.user.isGM && (!game.users.activeGM || game.users.activeGM.id === game.user.id);
const button = (action, label, attrs = '') => `<button type="button" data-mr-action="${action}" ${attrs}>${esc(label)}</button>`;
const field = (name, label, value, area = false, help = '') => `<div class="mr-field"><label for="mr-${name}">${esc(label)}</label>${area ? `<textarea id="mr-${name}" name="${name}">${esc(value)}</textarea>` : `<input id="mr-${name}" name="${name}" value="${esc(value)}" maxlength="180">`}${help ? `<small>${esc(help)}</small>` : ''}</div>`;
const select = (name, label, value, options) => `<div class="mr-field"><label for="mr-${name}">${esc(label)}</label><select id="mr-${name}" name="${name}">${options.map(option => `<option value="${option}" ${value === option ? 'selected' : ''}>${esc(t(option))}</option>`).join('')}</select></div>`;
const empty = () => `<p class="mr-help">${esc(t('NoDocuments'))}</p>`;

function registry() {
  const id = game.settings.get(MOD, 'registryId');
  return game.journal.get(id) ?? game.journal.find(doc => doc.getFlag(MOD, 'registry') === true);
}

/** Convert original document prose to plain text for editable Narrator notes. */
function plainText(html) {
  const source = String(html ?? '').replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi, '')
    .replace(/<br\s*\/?\s*>|<\/(?:p|div|li|h[1-6])\s*>/gi, '\n');
  let result;
  if (typeof DOMParser !== 'undefined') {
    result = new DOMParser().parseFromString(source, 'text/html').body.textContent ?? '';
  } else {
    // Non-browser checks do not need a DOM; the UI escapes the result again.
    result = source.replace(/<[^>]*>/g, '').replace(/&(amp|lt|gt|quot|apos|nbsp);/g,
      (_match, entity) => ({amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",nbsp:' '})[entity]);
  }
  return result.replace(/[ \t]+\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
}

function initialNarratorCampaign() {
  const state = initialCampaign();
  const moduleActor = name => {
    const named = game.actors.getName?.(name);
    return named && belonging(named) ? named : docs('actors').find(actor => actor.name === name);
  };
  for (const vessel of state.vessels.slice(0, 6)) {
    const actor = moduleActor(vessel.name);
    if (actor) vessel.notes = [actor.system.shortDescription, actor.system.biography].map(plainText).filter(Boolean).join('\n\n').slice(0, 4000);
  }
  const neb = moduleActor('Neb-Sekhem');
  const notes = [];
  if (neb) {
    notes.push(plainText(neb.system.biography));
    for (const secret of neb.system.secrets ?? []) notes.push(`${plainText(secret.name)}: ${plainText(secret.description)}`);
    for (const threat of neb.system.threatsAndConsequences ?? []) {
      notes.push([plainText(threat.name), plainText(threat.description), ...(threat.list ?? []).map(plainText)].filter(Boolean).join('\n'));
    }
  }
  const banquet = docs('journal').find(journal => journal.getFlag(MOD, 'slug') === 'sesion2');
  const pages = banquet?.pages?.contents ?? banquet?.pages ?? [];
  for (const page of pages) {
    if (/^tentaci[oó]n\b/i.test(page.name)) notes.push(`${plainText(page.name)}\n${plainText(page.text?.content).slice(0, 900)}`);
  }
  state.nebNotes = notes.filter(Boolean).join('\n\n').slice(0, 12000);
  return state;
}

/** Client-scope settings use this browser's local storage, never the world database. */
function localIdentity() { return `${game.world.id}:${game.user.id}`; }
function readLocalKey() {
  if (!game.user.isGM) return undefined;
  return game.settings.get(MOD,'privateKeys')?.[localIdentity()];
}
async function ensureLocalKey() {
  if (!game.user.isGM) throw new Error(t('GMOnly'));
  let key = readLocalKey();
  if (!key) {
    key = await createPrivateKey();
    await game.settings.set(MOD,'privateKeys',{...game.settings.get(MOD,'privateKeys'),[localIdentity()]:key});
  }
  return key;
}

function setCampaignCache(document, state, envelope) {
  campaignCache = normalizeCampaign(state); campaignCacheId = document.id;
  campaignVaultFingerprint = JSON.stringify(envelope); campaignLocked = false;
}

/** No document ownership flag prevents raw world data from reaching other clients. */
async function loadPrivateCampaign(document) {
  if (!game.user.isGM || !document) return;
  const envelope = document.getFlag(MOD,'privateCampaign');
  if (campaignCacheId === document.id && campaignVaultFingerprint === JSON.stringify(envelope) && campaignCache) return;
  // Coalesce events while a migration writes its encrypted replacement.
  if (pendingVaultLoad) return pendingVaultLoad;
  pendingVaultLoad = (async () => {
    campaignCache = null; campaignCacheId = document.id; campaignLocked = true;
    if (envelope) {
      const key = readLocalKey();
      if (!key) return; // Never generate a replacement key for an existing encrypted campaign.
      try { setCampaignCache(document,await decryptCampaign(envelope,key),envelope); }
      catch (error) { console.warn(`${MOD} | private campaign remains locked`,error.name); }
      return;
    }
    const legacy = document.getFlag(MOD,'campaign');
    if (!legacy || !activeNarrator()) return;
    // Migration is a single document update: install ciphertext and remove plaintext.
    const encrypted = await encryptCampaign(legacy,await ensureLocalKey());
    await document.update({[`flags.${MOD}.privateCampaign`]:encrypted,[`flags.${MOD}.-=campaign`]:null});
    setCampaignCache(document,legacy,encrypted);
  })();
  try { await pendingVaultLoad; } finally { pendingVaultLoad = null; }
}

async function ensureRegistry() {
  if (!activeNarrator()) { const document=registry(); await loadPrivateCampaign(document); return document; }
  let document = registry();
  if (document) { await loadPrivateCampaign(document); return document; }
  const state = initialNarratorCampaign();
  const envelope = await encryptCampaign(state,await ensureLocalKey());
  document = await JournalEntry.create({
    name: t('RegistryTitle'), ownership: { default: CONST.DOCUMENT_OWNERSHIP_LEVELS.NONE },
    pages: [{name:t('RegistryTitle'),type:'text',text:{format:1,content:`<p>${esc(t('RegistryHelp'))}</p>`}}],
    flags: {[MOD]: {registry:true,privateCampaign:envelope}}
  });
  await game.settings.set(MOD,'registryId',document.id);
  setCampaignCache(document,state,envelope);
  return document;
}

function campaign() {
  if (!game.user.isGM || campaignLocked || !campaignCache) throw new Error(t('PrivateLocked'));
  return normalizeCampaign(campaignCache);
}
async function saveCampaign(value) {
  if (!activeNarrator()) throw new Error(t('ActiveGMOnly'));
  if (campaignLocked || !campaignCache) throw new Error(t('PrivateLocked'));
  campaignQueue = campaignQueue.catch(() => {}).then(async () => {
    const document = await ensureRegistry();
    const key = readLocalKey();
    if (!key || campaignLocked) throw new Error(t('PrivateLocked'));
    const next = normalizeCampaign(value);
    next.modifiedBy = game.user.name; next.modifiedAt = new Date().toISOString();
    const envelope = await encryptCampaign(next,key);
    await document.setFlag(MOD,'privateCampaign',envelope);
    setCampaignCache(document,next,envelope);
  });
  return campaignQueue;
}

function backupForm({locked=false}={}) {
  return `<section class="mr-paper"><h2>${esc(t(locked ? 'PrivateLocked' : 'PrivateBackup'))}</h2><p>${esc(t(locked ? 'PrivateLockedHelp' : 'PrivateBackupHelp'))}</p><p class="mr-help">${esc(t('PrivateBackupWarning'))}</p><form data-private-backup>${field('privateBackup',t('PastePrivateBackup'),'',true)}<div class="mr-actions">${!locked ? button('exportPrivate',t('ExportPrivateBackup')) : ''}${button('importPrivate',t('ImportPrivateBackup'),activeNarrator() ? '' : 'disabled')}</div></form>${!activeNarrator() ? `<p>${esc(t('ActiveGMOnly'))}</p>` : ''}</section>`;
}

async function exportPrivateBackup() {
  if (!game.user.isGM) throw new Error(t('GMOnly'));
  const data = makeCampaignBackup(campaign(),{worldId:game.world.id,userId:game.user.id});
  const blob = new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = `mr-trono-private-${game.world.id.replace(/[^a-z0-9_-]/gi,'_')}.json`;
  link.click(); setTimeout(() => URL.revokeObjectURL(url),1000);
}

export async function importPrivateBackup(input) {
  if (!activeNarrator()) throw new Error(t('ActiveGMOnly'));
  let backup;
  try { backup = parseCampaignBackup(input); } catch { throw new Error(t('InvalidPrivateBackup')); }
  const confirmed = await DialogV2.confirm({window:{title:t('ImportPrivateBackup')},content:`<p>${esc(t('RestorePrivateWarning'))}</p>`,yes:{label:t('Import')},no:{label:t('Cancel')},rejectClose:false});
  if (!confirmed) return false;
  const document = registry();
  if (!document) throw new Error(t('NoPrivateRegistry'));
  const envelope = await encryptCampaign(backup.campaign,await ensureLocalKey());
  await document.update({[`flags.${MOD}.privateCampaign`]:envelope,[`flags.${MOD}.-=campaign`]:null});
  setCampaignCache(document,backup.campaign,envelope);
  refreshBooks(); return true;
}

function isOurAdventure(adventure) {
  return adventure?.pack === PACK || adventure?.compendium?.collection === PACK || adventure?.getFlag?.(MOD, 'source') === MOD;
}

/** Additive imports preserve the user's documents even when using the core importer. */
Hooks.on('preImportAdventure', (adventure, _form, _toCreate, toUpdate) => {
  if (!isOurAdventure(adventure)) return;
  const count = discardUpdates(toUpdate);
  if (count) ui.notifications.info(fmt('Preserved', {count}));
});
Hooks.on('importAdventure', (adventure) => {
  if (!isOurAdventure(adventure) || !game.user.isGM) return;
  void game.settings.set(MOD, 'imported', true).catch(error => console.error(MOD, error));
});

export function emptyWorld() {
  const noDocuments = ['actors','journal','playlists','macros','tables','cards'].every(key => !game[key]?.size);
  // Mist Engine creates this native helper asynchronously for its current scene.
  // Every other Item remains user content and prevents the first-run offer.
  const onlyNativeHelpers = game.items.contents.every(item => item.type === 'scene-data');
  const onlyWelcomeScene = game.scenes.contents.every(scene => scene.id === 'NUEDEFAULTSCENE0' && scene.background?.src?.startsWith('nue/defaultscene/') && !scene.tokens.size);
  return noDocuments && onlyNativeHelpers && onlyWelcomeScene;
}

export async function importAdventure() {
  if (!game.user.isGM) return ui.notifications.warn(t('GMOnly'));
  if (!activeNarrator()) return ui.notifications.warn(t('ActiveGMOnly'));
  if (importing) return;
  importing = true;
  try {
    const pack = game.packs.get(PACK);
    if (!pack) throw new Error(t('MissingPack'));
    const adventure = (await pack.getDocuments())[0];
    if (!adventure) throw new Error(t('MissingAdventure'));
    // prepareImport is the v13 public API, yielding toCreate/toUpdate per document type.
    const prepared = await adventure.prepareImport({importFields: []});
    const additions = Object.values(prepared.toCreate).reduce((sum, list) => sum + list.length, 0);
    const preserved = Object.values(prepared.toUpdate).reduce((sum, list) => sum + list.length, 0);
    if (!additions) { ui.notifications.info(t('AlreadyImported')); return; }
    const accepted = await DialogV2.confirm({
      window: {title: t('ImportTitle'), icon: 'fa-solid fa-file-import'},
      content: `<p>${esc(fmt('ImportExplanation', {additions, preserved}))}</p>`,
      yes: {label: t('Import')}, no: {label: t('Cancel')}, rejectClose: false
    });
    if (!accepted) return;
    // Use the Adventure workflow so folder ordering and references remain native.
    await adventure.import({dialog: false});
    await game.settings.set(MOD, 'imported', true);
    await upgradeArtwork();
    await upgradeDirection();
    await upgradeEditorial();
    await ensureRegistry();
    ui.notifications.info(t('ImportDone'));
    openGMBook();
  } catch (error) { console.error(`${MOD} | import`, error); ui.notifications.error(error.message); }
  finally { importing = false; }
}

class BookBase extends ApplicationV2 {
  static DEFAULT_OPTIONS = {
    classes: ['mr-trono-book'], tag: 'section',
    position: {width: 940, height: 720},
    window: {resizable: true, minimizable: true, icon: 'fa-solid fa-book-open'}
  };
  page = 'home'; dirty = false; message = '';
  constructor(options = {}) {
    const saved = game.settings.get(MOD, 'positions')?.[new.target.name] ?? {};
    super({...options, position: {...saved, ...options.position}});
    books.add(this);
  }
  async _renderHTML() {
    const root = document.createElement('div');
    root.className = 'mr-book';
    root.innerHTML = await this.content();
    return root;
  }
  _replaceHTML(result, content) { content.replaceChildren(result); }
  async _onRender() {
    this.element.classList.toggle('mr-static', !game.settings.get(MOD, 'animations'));
    const body = this.element.querySelector('.mr-book');
    body.addEventListener('click', event => {
      const target = event.target.closest('[data-mr-action]');
      if (!target || !this.element.contains(target)) return;
      event.preventDefault();
      target.disabled = true;
      Promise.resolve(this.action(target.dataset.mrAction, target)).catch(error => {
        console.error(MOD, error); ui.notifications.error(error.message);
      }).finally(() => { if (target.isConnected) target.disabled = false; });
    });
    // Register listeners on the newly replaced inner node, avoiding listeners stacking on the frame.
    body.addEventListener('input', () => { this.dirty = true; });
    body.querySelectorAll('form').forEach(form => form.addEventListener('submit', event => event.preventDefault()));
  }
  async _preClose() {
    const pos = {...game.settings.get(MOD, 'positions')};
    pos[this.constructor.name] = Object.fromEntries(['width','height','top','left'].filter(key => Number.isFinite(this.position[key])).map(key => [key, this.position[key]]));
    await game.settings.set(MOD, 'positions', pos);
  }
  _onClose() { books.delete(this); }
  header(title, subtitle) {
    return `<header><img class="mr-mark" src="modules/${MOD}/brand/MR_09_Monograma_Marfil_Transparente.png" alt="MR" draggable="false"><div class="mr-kicker">MR · El Trono de la Sed</div><h1>${esc(title)}</h1><p>${esc(subtitle)}</p></header>`;
  }
  navigation(entries) {
    return `<nav class="mr-nav" aria-label="${esc(t('BookNavigation'))}">${entries.map(([key, label]) => button('nav', t(label), `data-page="${key}" ${this.page === key ? 'aria-current="page"' : ''}`)).join('')}</nav>`;
  }
  live() { return `<p class="mr-live" role="status" aria-live="polite">${esc(this.message)}</p>`; }
  async action(action, target) {
    if (action === 'nav') {
      if (this.dirty) return ui.notifications.warn(t('SaveBeforeNavigation'));
      this.page = target.dataset.page; this.message = ''; return this.render({force: true});
    }
    if (action === 'memories') return openMemories(target.dataset.actor);
    if (action === 'document') return openDocument(target.dataset.collection, target.dataset.id);
    if (action === 'scene') {
      if (!game.user.isGM) return;
      const scene = game.scenes.get(target.dataset.id);
      if (scene) await scene.view();
    }
    if (action === 'activateScene') {
      if (!game.user.isGM) return;
      const scene = game.scenes.get(target.dataset.id);
      if (scene) await scene.activate();
    }
    if (action === 'show') {
      if (!game.user.isGM) return;
      const journal = game.journal.get(target.dataset.id);
      if (!journal || journal.getFlag(MOD, 'audience') !== 'players') return;
      await journal.show(true);
    }
    if (action === 'playlist') {
      if (!game.user.isGM) return;
      const playlist = game.playlists.get(target.dataset.id);
      if (playlist) await (playlist.playing ? playlist.stopAll() : playlist.playAll());
    }
    if (action === 'exportPrivate') return exportPrivateBackup();
    if (action === 'importPrivate') {
      const data = new FormData(target.closest('form'));
      if (await importPrivateBackup(data.get('privateBackup'))) { this.dirty=false; this.message=t('Saved'); return this.render({force:true}); }
      return;
    }
    if (action === 'import') return importAdventure();
    if (action === 'tutorialGM') return startTutorial('narrator');
    if (action === 'tutorialPlayer') return startTutorial('players');
    if (action === 'discard') { this.dirty = false; this.message = t('ChangesDiscarded'); return this.render({force: true}); }
  }
  documentList(collection, list = docs(collection)) {
    if (!list.length) return empty();
    return `<ul class="mr-doclist">${list.map(doc => `<li>${doc.getFlag?.(MOD, 'thumbnail') ? `<img class="mr-doc-thumb" src="${esc(doc.getFlag(MOD, 'thumbnail'))}" alt="">` : ''}${button('document', doc.name, `data-collection="${collection}" data-id="${esc(doc.id)}"`)}${collection === 'scenes' ? button('scene', t('View'), `data-id="${esc(doc.id)}" title="${esc(t('ViewHelp'))}"`) + button('activateScene', t('Activate'), `data-id="${esc(doc.id)}" title="${esc(t('ActivateHelp'))}"`) : ''}${collection === 'journal' && doc.getFlag(MOD, 'audience') === 'players' ? button('show', t('ShowPlayers'), `data-id="${esc(doc.id)}"`) : ''}</li>`).join('')}</ul>`;
  }
}

class BookGM extends BookBase {
  static DEFAULT_OPTIONS = {id: 'mr-trono-gm', window: {title: 'MRTRONO.BookOfDead'}};
  _canRender() { if (!game.user.isGM) return false; }
  async content() {
    if (!game.user.isGM) return '';
    const document = registry();
    if (!document) return this.header(t('BookOfDead'),t('NarratorOnly')) + `<section class="mr-paper">${button('import',t('ImportTitle'))}</section>`;
    await loadPrivateCampaign(document);
    if (campaignLocked || !campaignCache) return this.header(t('BookOfDead'),t('NarratorOnly')) + backupForm({locked:true});
    const state = campaign();
    let body = '';
    if (this.page === 'home') body = `<div class="mr-grid"><section class="mr-paper"><h2>${esc(t('Campaign'))}</h2>${this.stateForm(state)}</section><section class="mr-paper"><h2>${esc(t('Sessions'))}</h2>${this.documentList('journal', docs('journal').filter(doc => /sesión|sesion|guía|guia|desenlace|epílogo/i.test(doc.name)))}<h3>${esc(t('Installation'))}</h3>${button('import', t('ImportTitle'))}<p class="mr-help">${esc(t('ImportHelp'))}</p></section></div>`;
    if (this.page === 'altar') body = `<form data-campaign><h2>${esc(t('Altar'))}</h2><p>${esc(t('AltarHelp'))}</p><div class="mr-altar">${state.vessels.map((v, i) => `<section class="mr-vessel" data-state="${v.state}"><img class="mr-vessel-art" src="modules/mr-trono-de-la-sed/assets/objects/vasija-${['hori','paser','tamerit','kasa','beset','dedi','septima'][i]}.webp" alt="" loading="lazy"><h3>${esc(v.name)}</h3>${i === 6 ? field('vessel6name', t('SeventhName'), v.name) : ''}${select(`vessel${i}state`, t('Situation'), v.state, ['captive','freed','lost','empty'])}${field(`vessel${i}notes`, t('VictimNotes'), v.notes, true)}</section>`).join('')}</div>${this.saveButtons('saveAltar')}</form>`;
    if (this.page === 'heroes') body = `<div class="mr-grid">${heroActors().map(actor => `<section class="mr-paper"><h2>${esc(actor.name)}</h2>${button('document', t('OfficialSheet'), `data-collection="actors" data-id="${actor.id}"`)} ${button('memories', t('BookOfMemories'), `data-actor="${actor.id}"`)}${this.statusList(actor)}</section>`).join('')}</div><section class="mr-paper"><h2>${esc(t('Challenges'))}</h2>${this.documentList('actors', docs('actors').filter(actor => !heroActors().includes(actor)))}</section>`;
    if (this.page === 'documents') body = `<div class="mr-grid"><section class="mr-paper"><h2>${esc(t('Scenes'))}</h2>${this.documentList('scenes')}<h2>${esc(t('Sound'))}</h2>${docs('playlists').map(p => button('playlist', `${t(p.playing ? 'Stop' : 'Play')}: ${p.name}`, `data-id="${p.id}"`)).join('') || empty()}</section><section class="mr-paper"><h2>${esc(t('Journals'))}</h2>${this.documentList('journal')}<h2>${esc(t('ObjectsTechniques'))}</h2>${this.documentList('items')}</section></div>`;
    if (this.page === 'neb') body = `<div class="mr-grid"><section class="mr-paper"><h2>${esc(t('NebPanel'))}</h2>${this.documentList('actors', docs('actors').filter(doc => /Neb.Sekhem|Khety|Merit|Serekh/.test(doc.name)))}${this.documentList('journal', docs('journal').filter(doc => /Neb.Sekhem|banquete|verdad|secreto|Merit|desenlace/i.test(doc.name)))}<p class="mr-help">${esc(t('NebPanelHelp'))}</p></section><section class="mr-paper"><form data-campaign>${field('nebNotes', t('Tentations'), state.nebNotes, true)}${this.saveButtons('saveNeb')}</form></section></div>`;
    if (this.page === 'guide') body = this.guide() + backupForm();
    return this.header(t('BookOfDead'), t('NarratorOnly')) + this.navigation([['home','Campaign'],['altar','Altar'],['heroes','Heroes'],['documents','Documents'],['neb','NebPanel'],['guide','Guide']]) + body + this.live();
  }
  stateForm(state) {
    return `<form data-campaign>${select('session', t('Session'), state.session, ['1','2','3','epilogue'])}<div class="mr-grid">${select('ritual', t('Ritual'), state.ritual, ['preparation','seventh','coronation','stopped'])}${select('meritSeal', t('MeritSeal'), state.meritSeal, ['intact','threatened','broken','renewed'])}${select('priestSeal', t('PriestSeal'), state.priestSeal, ['intact','threatened','broken','renewed'])}${select('heart', t('Heart'), state.heart, ['protected','exposed','destroyed','taken'])}</div>${field('threats', t('ActiveThreats'), state.threats, true)}${field('clues', t('DiscoveredClues'), state.clues, true)}${field('notes', t('NarratorNotes'), state.notes, true)}${this.saveButtons('saveState')}</form>`;
  }
  saveButtons(action) {
    return `<div class="mr-actions">${button(action, t('Save'), activeNarrator() ? '' : 'disabled')}${button('discard', t('Discard'))}</div>${!activeNarrator() ? `<p>${esc(t('ActiveGMOnly'))}</p>` : ''}`;
  }
  statusList(actor) {
    const statuses = nativeStatuses(actor);
    return statuses.length ? `<ul class="mr-statuses">${statuses.map(status => `<li>${esc(status.name)} · ${status.tier}</li>`).join('')}</ul>` : `<p class="mr-help">${esc(t('NoStatuses'))}</p>`;
  }
  guide() {
    return `<section class="mr-paper"><h2>${esc(t('Guide'))}</h2><ol>${['Guide1','Guide2','Guide3','Guide4','Guide5','Guide6'].map(key => `<li><p>${esc(t(key))}</p></li>`).join('')}</ol><div class="mr-actions">${button('nav', t('Campaign'), 'data-page="home"')}${button('nav', t('Heroes'), 'data-page="heroes"')}${button('nav', t('Documents'), 'data-page="documents"')}${button('tutorialGM', t('NarratorTutorial'))}${button('tutorialPlayer', t('PlayerTutorial'))}</div></section>`;
  }
  async action(action, target) {
    if (!game.user.isGM) return;
    if (['saveState','saveAltar','saveNeb'].includes(action)) {
      const data = new FormData(target.closest('form'));
      const state = campaign();
      if (action === 'saveState') for (const key of ['session','ritual','meritSeal','priestSeal','heart','threats','clues','notes']) state[key] = data.get(key);
      if (action === 'saveAltar') state.vessels = state.vessels.map((v,i) => ({name: i === 6 ? data.get('vessel6name') : v.name, state: data.get(`vessel${i}state`), notes: data.get(`vessel${i}notes`)}));
      if (action === 'saveNeb') state.nebNotes = data.get('nebNotes');
      await saveCampaign(state); this.dirty = false; this.message = t('Saved'); return this.render({force:true});
    }
    return super.action(action, target);
  }
}

class BookMemories extends BookBase {
  static DEFAULT_OPTIONS = {id: 'mr-trono-memories', window: {title: 'MRTRONO.BookOfMemories'}};
  actorId = '';
  selectedActor() {
    const list = heroActors().filter(own);
    // A permission change must never redirect an unsaved form into another Hero.
    return this.actorId ? list.find(actor => actor.id === this.actorId) : list[0];
  }
  async content() {
    let actor = this.selectedActor();
    if (!actor && this.actorId) { this.actorId = ''; actor = this.selectedActor(); }
    if (!actor) return this.header(t('BookOfMemories'), t('MemoriesHelp')) + `<section class="mr-paper"><p>${esc(t('NoOwnedHero'))}</p>${button('tutorialPlayer', t('PlayerTutorial'))}</section>`;
    this.actorId = actor.id;
    const memories = normalizeMemories(actor.getFlag(MOD, 'memories'));
    const statuses = nativeStatuses(actor);
    return this.header(t('BookOfMemories'), t('MemoriesHelp')) + `<nav class="mr-nav" aria-label="${esc(t('Heroes'))}">${heroActors().filter(own).map(hero => button('chooseActor', hero.name, `data-id="${hero.id}" ${hero.id === actor.id ? 'aria-current="page"' : ''}`)).join('')}</nav><section class="mr-paper"><h2>${esc(actor.name)}</h2>${button('tutorialPlayer', t('PlayerTutorial'))}<h3>${esc(t('NativeStatuses'))}</h3>${statuses.length ? `<ul class="mr-statuses">${statuses.map(status => `<li>${esc(status.name)} · ${status.tier}</li>`).join('')}</ul>` : `<p>${esc(t('NoStatuses'))}</p>`}<p class="mr-help">${esc(t('NativeStatusesHelp'))}</p>${button('document', t('OfficialSheet'), `data-collection="actors" data-id="${actor.id}"`)}<hr><form data-memories>${field('trueName', t('TrueName'), memories.trueName || actor.name)}${field('bonds', t('Bonds'), memories.bonds, true)}${memories.entries.map((entry,i) => `<article class="mr-memory ${entry.condition === 'threatened' ? 'mr-memory-glow' : ''}" data-state="${entry.condition}"><span class="mr-memory-state">${esc(t(entry.condition))}</span>${field(`title${i}`, t('MemoryTitle'), entry.title)}${field(`detail${i}`, t('MemoryDetail'), entry.detail, true)}${field(`anchor${i}`, t('IdentityAnchor'), entry.anchor)}${select(`condition${i}`, t('MemoryCondition'), entry.condition, ['established','threatened','recovered'])}${button('deleteMemory', t('RemoveMemory'), `data-index="${i}"`)}</article>`).join('')}${field('changes', t('NarrativeChanges'), memories.changes, true)}<div class="mr-actions">${button('saveMemories', t('Save'))}${button('addMemory', t('AddMemory'))}${button('discard', t('Discard'))}</div><p class="mr-help">${esc(t('PerceivedOnly'))}</p></form>${this.live()}</section>`;
  }
  formMemories() {
    const actor = this.selectedActor();
    const current = normalizeMemories(actor.getFlag(MOD, 'memories'));
    const data = new FormData(this.element.querySelector('[data-memories]'));
    return normalizeMemories({trueName: data.get('trueName'), bonds: data.get('bonds'), changes: data.get('changes'), entries: current.entries.map((entry,i) => ({title: data.get(`title${i}`), detail: data.get(`detail${i}`), anchor: data.get(`anchor${i}`), condition: data.get(`condition${i}`)}))});
  }
  async action(action, target) {
    if (action === 'chooseActor') {
      if (this.dirty) return ui.notifications.warn(t('SaveBeforeNavigation'));
      this.actorId = target.dataset.id; this.message = ''; return this.render({force:true});
    }
    if (['saveMemories','addMemory','deleteMemory'].includes(action)) {
      const actor = this.selectedActor();
      if (!own(actor)) throw new Error(t('OwnerOnly'));
      const next = this.formMemories();
      if (action === 'addMemory') next.entries.push({title:'', detail:'', anchor:'', condition:'established'});
      if (action === 'deleteMemory') next.entries.splice(Number(target.dataset.index),1);
      await actor.setFlag(MOD, 'memories', normalizeMemories(next));
      this.dirty = false; this.message = t('Saved'); return this.render({force:true});
    }
    return super.action(action, target);
  }
}

/** Native Foundry tours prepare each real panel before looking up its selector. */
class TronoTour extends foundry.nue.Tour {
  constructor(config, options = {}) {
    super(config, options);
    this.originalSelectors = new Map(config.steps.map(step => [step.id, step.selector]));
  }
  async start() {
    const book = this.id === 'narrator' ? gmBook : memoryBook;
    if (book?.dirty) return ui.notifications.warn(t('SaveBeforeNavigation'));
    return super.start();
  }
  async _preStep() {
    await super._preStep();
    const step = this.currentStep;
    if (!step) return;
    if (this.id === 'narrator') {
      if (!game.user.isGM) throw new Error(t('GMOnly'));
      gmBook ??= new BookGM();
      if (gmBook.dirty) throw new Error(t('SaveBeforeNavigation'));
      gmBook.page = ({welcome:'home',campaign:'home',heroes:'heroes',altar:'altar',documents:'documents',neb:'neb',finish:'guide'})[step.id] ?? 'home';
      books.add(gmBook); await gmBook.render({force:true});
      gmBook.bringToFront();
    } else {
      memoryBook ??= new BookMemories();
      books.add(memoryBook); await memoryBook.render({force:true});
      memoryBook.bringToFront();
    }
    const selector = this.originalSelectors.get(step.id);
    // Unassigned Heroes have no memory form yet: explain centrally instead of failing.
    step.selector = selector && document.querySelector(selector) ? selector : '';
  }
}

async function registerTours() {
  for (const id of ['narrator','players']) {
    if (game.tours.has(`${MOD}.${id}`)) continue;
    const tour = await TronoTour.fromJSON(`modules/${MOD}/tours/${id}.json`);
    game.tours.register(MOD, id, tour);
  }
}

export async function startTutorial(id = game.user.isGM ? 'narrator' : 'players') {
  if (!['narrator','players'].includes(id)) return;
  if (id === 'narrator' && !game.user.isGM) return ui.notifications.warn(t('GMOnly'));
  const book = id === 'narrator' ? gmBook : memoryBook;
  if (book?.dirty) return ui.notifications.warn(t('SaveBeforeNavigation'));
  try {
    await registerTours();
    const current = foundry.nue.Tour.activeTour;
    if (current) await current.exit();
    const tour = game.tours.get(`${MOD}.${id}`);
    await tour.reset();
    // Opening the correct book precedes the native Tour, even when started via API.
    if (id === 'narrator') await openGMBook(); else await openMemories();
    return tour.start();
  } catch (error) { console.error(`${MOD} | tutorial`, error); ui.notifications.error(error.message); }
}

class TutorialMenu extends BookBase {
  static DEFAULT_OPTIONS = {id:'mr-trono-tutorials',position:{width:560,height:350},window:{title:'MRTRONO.Tutorials'}};
  async content() {
    return this.header(t('Tutorials'), t('TutorialsHelp')) + `<section class="mr-paper"><div class="mr-actions">${game.user.isGM ? button('tutorialGM',t('NarratorTutorial')) : ''}${button('tutorialPlayer',t('PlayerTutorial'))}</div></section>`;
  }
}

function openDocument(collection, id) {
  if (!['actors','items','journal','scenes','playlists'].includes(collection)) return;
  const doc = game[collection]?.get(id);
  if (!doc || (!game.user.isGM && !doc.testUserPermission(game.user, 'OBSERVER'))) return;
  return doc.sheet.render(true);
}
export function openGMBook() {
  if (!game.user.isGM) return ui.notifications.warn(t('GMOnly'));
  gmBook ??= new BookGM(); books.add(gmBook); return gmBook.render({force:true});
}
export function openMemories(actorId) {
  memoryBook ??= new BookMemories();
  if (actorId && own(game.actors.get(actorId))) memoryBook.actorId = actorId;
  books.add(memoryBook); return memoryBook.render({force:true});
}

Hooks.once('init', () => {
  game.settings.register(MOD, 'imported', {scope:'world', config:false, type:Boolean, default:false});
  game.settings.register(MOD,'privateKeys',{scope:'client',config:false,type:Object,default:{}});
  game.settings.register(MOD, 'registryId', {scope:'world', config:false, type:String, default:''});
  game.settings.register(MOD, 'offered', {scope:'client', config:false, type:Boolean, default:false});
  game.settings.register(MOD, 'positions', {scope:'client', config:false, type:Object, default:{}});
  game.settings.register(MOD, 'animations', {name:'MRTRONO.Animations', hint:'MRTRONO.AnimationsHelp', scope:'client', config:true, type:Boolean, default:false, onChange: () => refreshBooks()});
  game.settings.registerMenu(MOD, 'gmBook', {name:'MRTRONO.BookOfDead', label:'MRTRONO.Open', hint:'MRTRONO.NarratorOnly', icon:'fa-solid fa-book-skull', type:BookGM, restricted:true});
  game.settings.registerMenu(MOD, 'tutorials', {name:'MRTRONO.Tutorials', label:'MRTRONO.Open', hint:'MRTRONO.TutorialsHelp', icon:'fa-solid fa-graduation-cap', type:TutorialMenu, restricted:false});
  game.settings.registerMenu(MOD, 'memories', {name:'MRTRONO.BookOfMemories', label:'MRTRONO.Open', hint:'MRTRONO.MemoriesHelp', icon:'fa-solid fa-book-open', type:BookMemories, restricted:false});
  game.keybindings.register(MOD, 'memories', {name:'MRTRONO.BookOfMemories', editable:[{key:'KeyM', modifiers:['Alt']}], onDown: () => {openMemories(); return true;}});
  game.keybindings.register(MOD, 'book', {name:'MRTRONO.BookOfDead', editable:[{key:'KeyB', modifiers:['Alt']}], restricted:true, onDown: () => {openGMBook(); return true;}});
});

function refreshBooks() {
  for (const book of books) if (book.rendered && !book.dirty) void book.render({force:true});
}
for (const hook of ['updateActor','createActor','deleteActor','updateScene','updatePlaylist']) Hooks.on(hook,refreshBooks);
Hooks.on('updateJournalEntry', async document => {
  if (game.user.isGM && document.getFlag(MOD,'registry')) {
    // Do not await an in-flight migration from its own update event.
    if (!pendingVaultLoad) await loadPrivateCampaign(document);
  }
  refreshBooks();
});
Hooks.once('ready', async () => {
  game.modules.get(MOD).api = Object.freeze({openGMBook, openMemories, importAdventure, startTutorial,openSceneGuide,dispatchDirector});
  if (game.system.id !== 'mist-engine-fvtt') { ui.notifications.error(t('WrongSystem')); return; }
  await upgradeArtwork();
  if (globalThis.Scene) {
    try {await upgradeDirection();await upgradeEditorial();}
    catch(error){console.error(`${MOD} | editorial upgrade`,error);ui.notifications.warn(t('EditorialUpgradeFailed'));}
  }
  setupDirector();
  try { await registerTours(); } catch (error) { console.error(`${MOD} | register tours`, error); ui.notifications.warn(t('ToursUnavailable')); }
  // Offer only once and only to the active GM. Existing worlds use the manual menu.
  const offer = activeNarrator() && !game.settings.get(MOD, 'offered') && !game.settings.get(MOD, 'imported') && emptyWorld();
  if (offer) {
    await game.settings.set(MOD, 'offered', true);
    await importAdventure();
  } else if (game.user.isGM && game.settings.get(MOD,'imported')) await ensureRegistry();
});

Hooks.once('init',()=>{registerPresentation();registerDirector();});
