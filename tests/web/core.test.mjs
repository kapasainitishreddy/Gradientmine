import test from 'node:test';
import assert from 'node:assert/strict';
import { b58encode, b58decode, solToLamports, explorer, verifyEnvelope, sha256, equal } from '../../web/assets/core.mjs';

test('base58 preserves leading zeros and rejects invalid input', () => {
  for (const raw of [new Uint8Array(32), new Uint8Array([0, 0, 255, 2]), crypto.getRandomValues(new Uint8Array(64))]) assert.deepEqual(b58decode(b58encode(raw)), raw);
  assert.throws(() => b58decode('0OIl'));
});
test('SOL amounts are parsed as exact decimal integers, not floating multiplication', () => {
  assert.equal(solToLamports('0.025'), 25000000);
  assert.equal(solToLamports('1'), 1000000000);
  assert.equal(solToLamports('0.000000001'), 1);
  for (const bad of ['1e-3', '-1', '0.0000000001', '1.000000001', '', 'NaN']) assert.throws(() => solToLamports(bad));
});
test('Explorer never fabricates links for local mode or invalid signatures', () => {
  const signature = b58encode(new Uint8Array(64).fill(1));
  assert.equal(explorer('local', signature), null);
  assert.equal(explorer('devnet', 'not-a-transaction'), null);
  assert.equal(explorer('devnet', signature), `https://explorer.solana.com/tx/${signature}?cluster=devnet`);
  assert.equal(explorer('devnet', 'javascript:alert(1)', 'address'), null);
});
test('signed payload must match bytes, expected signer and signature', async () => {
  const pair = await crypto.subtle.generateKey('Ed25519', true, ['sign', 'verify']);
  const signer = b58encode(new Uint8Array(await crypto.subtle.exportKey('raw', pair.publicKey)));
  const payload = {score: 0.95, worker: 'test'};
  const bytes = new TextEncoder().encode(JSON.stringify(payload));
  const envelope = {payload, signer, payload_base64: Buffer.from(bytes).toString('base64'), signature: Buffer.from(await crypto.subtle.sign('Ed25519', pair.privateKey, bytes)).toString('base64')};
  assert.equal(await verifyEnvelope(envelope, signer), true);
  assert.equal(await verifyEnvelope({...envelope, payload: {...payload, score:1}}, signer), false);
  assert.equal(await verifyEnvelope(envelope, b58encode(new Uint8Array(32))), false);
  assert.equal(await verifyEnvelope({...envelope, signature:Buffer.alloc(64).toString('base64')}, signer), false);
  assert.equal(await sha256(new TextEncoder().encode('abc')), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad');
  assert.equal(equal({a:1,b:2},{b:2,a:1}),true);
});

test('auth challenge uses the exact API expires_at schema, origin and wallet-bound text',async()=>{
 const {messageChallenge}=await import('../../web/assets/core.mjs');
 const expires=Math.floor(Date.now()/1000)+300,origin='http://localhost:8000',address='abc',nonce='a'.repeat(43);
 const message=`GradientMine wallet authentication v1\nOrigin: ${origin}\nWallet: ${address}\nNonce: ${nonce}\nExpires: ${expires}\nThis message authenticates a session. It does not authorize a transaction.`;
 const c={nonce,expires_at:expires,message};
 assert.equal(new TextDecoder().decode(messageChallenge(c,origin,address)),message);
 assert.throws(()=>messageChallenge(c,'https://wrong.example',address));
 assert.throws(()=>messageChallenge({...c,expires_at:0},origin,address));
});
