import test from 'node:test';
import assert from 'node:assert/strict';
import {initialCampaign} from '../js/state.mjs';
import {createPrivateKey,encryptCampaign,decryptCampaign,makeCampaignBackup,parseCampaignBackup} from '../js/private-store.mjs';

test('AES-GCM roundtrip keeps private campaign strings out of the transmitted envelope', async () => {
  const key=await createPrivateKey();const state=initialCampaign();state.notes='PRIVATE_NARRATOR_CANARY';state.vessels[0].notes='Hori was freed secretly';
  const encrypted=await encryptCampaign(state,key);
  assert.deepEqual(Object.keys(encrypted).sort(),['ciphertext','iv','v']);
  assert.doesNotMatch(JSON.stringify(encrypted),/PRIVATE_NARRATOR_CANARY|Hori/);
  assert.deepEqual(await decryptCampaign(encrypted,key),state);
});

test('repeated writes use distinct random IVs even with the same key and notes', async () => {
  const key=await createPrivateKey();const state=initialCampaign();
  const a=await encryptCampaign(state,key),b=await encryptCampaign(state,key);
  assert.notEqual(a.iv,b.iv);assert.notEqual(a.ciphertext,b.ciphertext);
});

test('missing and wrong keys reject decryption without modifying the envelope', async () => {
  const envelope=await encryptCampaign(initialCampaign(),await createPrivateKey());const before=JSON.stringify(envelope);
  await assert.rejects(decryptCampaign(envelope,undefined),/missing/);
  await assert.rejects(decryptCampaign(envelope,await createPrivateKey()));
  assert.equal(JSON.stringify(envelope),before);
});

test('authenticated encryption rejects tampering and malformed envelopes', async () => {
  const key=await createPrivateKey();const envelope=await encryptCampaign(initialCampaign(),key);
  const altered={...envelope,ciphertext:(envelope.ciphertext[0]==='A'?'B':'A')+envelope.ciphertext.slice(1)};
  await assert.rejects(decryptCampaign(altered,key));
  await assert.rejects(decryptCampaign({...envelope,iv:'AA=='},key));
  await assert.rejects(decryptCampaign({...envelope,v:2},key));
});

test('local backup is portable plaintext, excludes encryption keys, and validates every vessel', () => {
  const state=initialCampaign();state.notes='LOCAL_BACKUP_CANARY';
  const backup=makeCampaignBackup(state,{worldId:'world',userId:'gm'});
  assert.equal(backup.campaign.notes,'LOCAL_BACKUP_CANARY');assert.equal('key' in backup,false);
  assert.deepEqual(parseCampaignBackup(JSON.stringify(backup)).campaign,state);
  backup.campaign.vessels[0].name='Changed Hori';
  assert.throws(()=>parseCampaignBackup(JSON.stringify(backup)),/vessel/);
});

test('backup parser rejects incomplete or silently defaulted campaign data', () => {
  assert.throws(()=>parseCampaignBackup('{}'));
  const backup=makeCampaignBackup(initialCampaign());backup.campaign.heart='invalid';
  assert.throws(()=>parseCampaignBackup(JSON.stringify(backup)),/heart/);
});
