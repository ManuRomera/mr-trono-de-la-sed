/** Pure helpers shared by the Foundry interface and its checks. No dice engine. */
export const MODULE_ID = 'mr-trono-de-la-sed';
export const VICTIMS = ['Hori', 'Paser', 'Tamerit', 'Kasa', 'Beset', 'Dedi', 'Séptimo nombre'];
export const MEMORY_STATES = ['established', 'threatened', 'recovered'];
export const VESSEL_STATES = ['captive', 'freed', 'lost', 'empty'];
export const escapeHTML = (value = '') => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
const text = (value, max = 12000) => String(value ?? '').slice(0, max);

/** Only perceived narrative information belongs on a player-owned Actor. */
export function normalizeMemories(raw = {}) {
  return {
    trueName: text(raw.trueName, 120),
    bonds: text(raw.bonds, 4000),
    changes: text(raw.changes, 6000),
    entries: (Array.isArray(raw.entries) ? raw.entries : []).slice(0, 60).map(entry => ({
      title: text(entry.title, 180), detail: text(entry.detail, 4000),
      anchor: text(entry.anchor, 600),
      condition: MEMORY_STATES.includes(entry.condition) ? entry.condition : 'established'
    }))
  };
}

/** Derive status intensity exactly from native markings; never cache a second tier. */
export function nativeStatuses(actor) {
  return (actor?.system?.floatingTagsAndStatuses ?? []).filter(tag => tag.isStatus).map(tag => {
    const markings = Array.isArray(tag.markings) ? tag.markings : [];
    const tier = markings.reduce((n, mark, i) => mark ? i + 1 : n, 0);
    return { name: text(tag.name, 180), tier, positive: Boolean(tag.positive) };
  });
}

export function initialCampaign() {
  return {
    schemaVersion: 1, session: '1', ritual: 'preparation',
    meritSeal: 'intact', priestSeal: 'intact', heart: 'protected',
    vessels: VICTIMS.map((name, i) => ({ name, state: i === 6 ? 'empty' : 'captive', notes: '' })),
    notes: '', threats: '', clues: '', nebNotes: '', modifiedBy: '', modifiedAt: ''
  };
}

export function normalizeCampaign(raw = {}) {
  const base = initialCampaign();
  const choice = (value, allowed, fallback) => allowed.includes(value) ? value : fallback;
  return {
    ...base,
    session: choice(String(raw.session), ['1', '2', '3', 'epilogue'], base.session),
    ritual: choice(raw.ritual, ['preparation', 'seventh', 'coronation', 'stopped'], base.ritual),
    meritSeal: choice(raw.meritSeal, ['intact', 'threatened', 'broken', 'renewed'], base.meritSeal),
    priestSeal: choice(raw.priestSeal, ['intact', 'threatened', 'broken', 'renewed'], base.priestSeal),
    heart: choice(raw.heart, ['protected', 'exposed', 'destroyed', 'taken'], base.heart),
    vessels: base.vessels.map((v, i) => ({
      name: i === 6 ? text(raw.vessels?.[i]?.name || v.name, 120) : v.name,
      state: choice(raw.vessels?.[i]?.state, VESSEL_STATES, v.state),
      notes: text(raw.vessels?.[i]?.notes, 4000)
    })),
    notes: text(raw.notes), threats: text(raw.threats), clues: text(raw.clues), nebNotes: text(raw.nebNotes),
    modifiedBy: text(raw.modifiedBy, 120), modifiedAt: text(raw.modifiedAt, 80)
  };
}

/** Adventures normally update matching IDs. This module imports additions only. */
export function discardUpdates(toUpdate) {
  let skipped = 0;
  for (const [name, documents] of Object.entries(toUpdate ?? {})) {
    skipped += Array.isArray(documents) ? documents.length : 0;
    delete toUpdate[name];
  }
  return skipped;
}
