/** Authenticated encryption for private campaign notes. Keys never enter world data. */
import {normalizeCampaign} from './state.mjs';
const encoder = new TextEncoder();
const decoder = new TextDecoder();
const AAD = encoder.encode('mr-trono-de-la-sed:campaign:v1');
const encode = bytes => {
  let binary = '';
  for (let i=0;i<bytes.length;i+=8192) binary += String.fromCharCode(...bytes.subarray(i,i+8192));
  return btoa(binary);
};
function decode(value, limit) {
  if (typeof value !== 'string' || value.length > limit || !/^[A-Za-z0-9+/]*={0,2}$/.test(value)) throw new Error('Invalid encrypted data');
  return Uint8Array.from(atob(value), char => char.charCodeAt(0));
}
export async function createPrivateKey() {
  if (!globalThis.crypto?.subtle) throw new Error('WebCrypto is unavailable');
  const key = await crypto.subtle.generateKey({name:'AES-GCM',length:256},true,['encrypt','decrypt']);
  return encode(new Uint8Array(await crypto.subtle.exportKey('raw',key)));
}
async function importKey(raw) {
  const bytes = decode(raw,64);
  if (bytes.byteLength !== 32) throw new Error('Invalid private key');
  return crypto.subtle.importKey('raw',bytes,{name:'AES-GCM'},false,['encrypt','decrypt']);
}
export async function encryptCampaign(campaign, rawKey) {
  const key = await importKey(rawKey);
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const plain = encoder.encode(JSON.stringify(normalizeCampaign(campaign)));
  const ciphertext = await crypto.subtle.encrypt({name:'AES-GCM',iv,additionalData:AAD,tagLength:128},key,plain);
  return {v:1,iv:encode(iv),ciphertext:encode(new Uint8Array(ciphertext))};
}
export async function decryptCampaign(envelope, rawKey) {
  if (!rawKey) throw new Error('Private key is missing');
  if (!envelope || envelope.v !== 1) throw new Error('Unsupported encrypted data');
  const iv = decode(envelope.iv,32);
  if (iv.byteLength !== 12) throw new Error('Invalid initialization vector');
  const ciphertext = decode(envelope.ciphertext,500000);
  const key = await importKey(rawKey);
  const plain = await crypto.subtle.decrypt({name:'AES-GCM',iv,additionalData:AAD,tagLength:128},key,ciphertext);
  return normalizeCampaign(JSON.parse(decoder.decode(plain)));
}

/** Backups are intentionally local plaintext, portable without the original browser key. */
export function makeCampaignBackup(campaign, {worldId='',userId=''}={}) {
  return {format:'mr-trono-campaign-backup',version:1,worldId,userId,exportedAt:new Date().toISOString(),campaign:normalizeCampaign(campaign)};
}
export function parseCampaignBackup(input) {
  if (typeof input !== 'string' || input.length > 250000) throw new Error('Invalid backup size');
  const data = JSON.parse(input);
  const state = data?.campaign;
  if (data?.format !== 'mr-trono-campaign-backup' || data.version !== 1 || !state || typeof state !== 'object' || Array.isArray(state)) throw new Error('Unsupported campaign backup');
  const expected = normalizeCampaign(state);
  for (const key of ['session','ritual','meritSeal','priestSeal','heart']) {
    if (state[key] !== expected[key]) throw new Error(`Invalid campaign field: ${key}`);
  }
  if (!Array.isArray(state.vessels) || state.vessels.length !== 7) throw new Error('Backup must contain seven vessels');
  state.vessels.forEach((v,i) => {
    if (!v || v.name !== expected.vessels[i].name || v.state !== expected.vessels[i].state || typeof v.notes !== 'string' || v.notes.length > 4000) throw new Error('Invalid vessel in backup');
  });
  for (const key of ['notes','threats','clues','nebNotes']) {
    if (typeof state[key] !== 'string' || state[key].length > 12000) throw new Error(`Invalid campaign notes: ${key}`);
  }
  return {campaign:expected,worldId:String(data.worldId??''),userId:String(data.userId??'')};
}
