import test from 'node:test';
import assert from 'node:assert/strict';
import {parsePending,recoverPending} from '../../web/assets/pending.mjs';
import {b58encode} from '../../web/assets/core.mjs';

const pending={job_id:'bounty-1',action:'fund',signature:b58encode(new Uint8Array(64).fill(1)),transaction_base64:'retained-exact-signed-bytes'};

test('lost broadcast response recovers by retrying the identical signed bytes after checking finalization',async()=>{
 const calls=[];
 const request=async(path,body)=>{calls.push({path,body});if(calls.length===1)throw Error('Signature not finalized');return {ok:true};};
 await recoverPending(pending,request);
 assert.deepEqual(calls,[
  {path:'/api/jobs/bounty-1/confirm',body:{action:'fund',signature:pending.signature}},
  {path:'/api/jobs/bounty-1/broadcast',body:{action:'fund',transaction_base64:pending.transaction_base64}},
  {path:'/api/jobs/bounty-1/confirm',body:{action:'fund',signature:pending.signature}},
 ]);
});

test('already finalized transactions are confirmed without another broadcast',async()=>{
 const calls=[];await recoverPending(pending,async(path)=>calls.push(path));
 assert.deepEqual(calls,['/api/jobs/bounty-1/confirm']);
});

test('failed or expired original bytes remain a failure and never request a new signature',async()=>{
 const calls=[];
 await assert.rejects(recoverPending(pending,async(path)=>{calls.push(path);throw Error('Expired original transaction');}),/Expired/);
 assert.deepEqual(calls,['/api/jobs/bounty-1/confirm','/api/jobs/bounty-1/broadcast']);
});

test('legacy confirmation-only records remain recoverable and malformed local storage is rejected',()=>{
 const context={jobId:'bounty-1',origin:'https://gradientmine.example',programId:'test-program'};
 const legacy={job_id:pending.job_id,action:pending.action,signature:pending.signature};
 assert.deepEqual(parsePending(JSON.stringify(legacy),context),legacy);
 for(const raw of ['{',JSON.stringify({...legacy,job_id:'another-bounty'}),JSON.stringify({...legacy,signature:'javascript:alert(1)'}),JSON.stringify({...legacy,action:'settle'}),JSON.stringify(pending),'x'.repeat(5000)])assert.equal(parsePending(raw,context),null);
});

test('retained signed bytes are bound to the exact origin, program, wallet and signature',async()=>{
 const {readFileSync}=await import('node:fs');
 const {bytes}=await import('../../web/assets/core.mjs');
 const f=JSON.parse(readFileSync(new URL('../fixtures/wallet-intent.json',import.meta.url)));
 const context={jobId:f.job.id,origin:'https://gradientmine.example',programId:f.intent.program_id};
 const p={version:1,origin:context.origin,job_id:f.job.id,action:'fund',signature:b58encode(bytes(f.signed).slice(1,65)),address:f.intent.payer,program_id:f.intent.program_id,transaction_base64:f.signed};
 assert.deepEqual(parsePending(JSON.stringify(p),context),p);
 for(const changed of [{origin:'https://another.example'},{program_id:'wrong-program'},{address:'wrong-wallet'},{signature:b58encode(new Uint8Array(64).fill(2))}])assert.equal(parsePending(JSON.stringify({...p,...changed}),context),null);
});
