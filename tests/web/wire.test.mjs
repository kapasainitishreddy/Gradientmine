import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validateIntent, validateWalletSignature, decodeLegacy} from '../../web/assets/wire.mjs';
import {bytes,base64} from '../../web/assets/core.mjs';
const f=JSON.parse(readFileSync(new URL('../fixtures/wallet-intent.json',import.meta.url)));
test('reconstructs an exact Devnet fund instruction from bounty policy',async()=>{
 const result=await validateIntent(f.intent,'fund',f.job,f.config,f.intent.payer);
 assert.equal(result.payer,f.intent.payer); assert.equal(result.instructions.length,1);
});
test('refuses changed rewards, program, signer, extra bytes and changed instruction bytes',async()=>{
 for(const mutate of [x=>x.job.policy.reward_lamports++,x=>x.config.mode='local',x=>x.intent.program_id='11111111111111111111111111111111',x=>x.intent.payer=x.job.policy.validator,x=>{let b=bytes(x.intent.transaction_base64);b[b.length-1]^=1;x.intent.transaction_base64=base64(b);},x=>x.intent.transaction_base64=base64(new Uint8Array([...bytes(x.intent.transaction_base64),0]))]) {
  const x=structuredClone(f);mutate(x);
  await assert.rejects(validateIntent(x.intent,'fund',x.job,x.config,f.intent.payer));
 }
});
test('wallet signature is checked against exactly the reviewed transaction',async()=>{
 await validateWalletSignature(bytes(f.intent.transaction_base64),bytes(f.signed),f.intent.payer);
 const changed=bytes(f.signed);changed[changed.length-1]^=1;
 await assert.rejects(validateWalletSignature(bytes(f.intent.transaction_base64),changed,f.intent.payer));
 await assert.rejects(validateWalletSignature(bytes(f.intent.transaction_base64),bytes(f.intent.transaction_base64),f.intent.payer));
});
test('rejects oversized, noncanonical and multisignature payloads',()=>{
 assert.throws(()=>decodeLegacy(new Uint8Array(1233)));
 assert.throws(()=>decodeLegacy(new Uint8Array([129,0,...bytes(f.intent.transaction_base64).slice(1)])));
 const multisig=bytes(f.intent.transaction_base64);multisig[0]=2;assert.throws(()=>decodeLegacy(multisig));
});
