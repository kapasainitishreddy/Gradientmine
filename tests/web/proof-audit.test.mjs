import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {auditLocalEvidence} from '../../web/assets/proof-audit.mjs';

const root=new URL('../../web/assets/',import.meta.url);
const run=JSON.parse(readFileSync(new URL('recorded-run.json',root),'utf8'));
const artifact=hash=>readFileSync(new URL('artifacts/'+hash+'.json',root));

test('real public local proof audits every artifact, signer and winner lineage',async()=>{
  const progress=[];
  const result=await auditLocalEvidence(run,async hash=>artifact(hash),step=>progress.push(step));
  assert.equal(result.status,'verified-public-evidence');
  assert.equal(result.artifactsVerified,14);
  assert.equal(result.signaturesVerified,6);
  assert.equal(result.policyMatches,true);
  assert.equal(result.winnerReferencesMatch,true);
  assert.equal(result.proofOfTraining,false);
  assert.equal(result.provedModelQuality,false);
  assert.equal(result.devnetPayment,false);
  assert.equal(progress.length,14);
  assert.deepEqual(progress.at(-1),{completed:14,total:14});
});

test('tampered artifact bytes are rejected before a signature/quality claim',async()=>{
  const altered=run.artifacts[0];
  await assert.rejects(auditLocalEvidence(run,async hash=>{
    const bytes=Buffer.from(artifact(hash));
    if(hash===altered)bytes[0]^=1;
    return bytes;
  }),/SHA-256 does not match/);
});

test('changed local record scores cannot borrow valid evaluator signatures',async()=>{
  const mutated=structuredClone(run);
  mutated.job.submissions[0].score.candidate_accuracy=.99;
  await assert.rejects(auditLocalEvidence(mutated,async hash=>artifact(hash)),
    /inconsistent score, signer or lineage/);
});

test('the audit refuses a fabricated settlement in a local experiment',async()=>{
  const mutated=structuredClone(run);
  mutated.job.settlement_signature='fictitious';
  await assert.rejects(auditLocalEvidence(mutated,async hash=>artifact(hash)),
    /Unexpected blockchain transaction/);
});

test('missing hashes never produce a successful green result',async()=>{
  const mutated=structuredClone(run);
  mutated.artifacts.pop();
  await assert.rejects(auditLocalEvidence(mutated,async hash=>artifact(hash)),
    /allowlist/);
});

test('judges can start audit only after recorded evidence loads; UI cannot fake success',()=>{
  const html=readFileSync(new URL('../../web/judge.html',import.meta.url),'utf8');
  const tour=readFileSync(new URL('../../web/assets/judge-tour.mjs',import.meta.url),'utf8');
  assert.match(html,/id="run-evidence-audit"[^>]+disabled/);
  assert.match(html,/id="evidence-audit-result" role="status"/);
  assert.match(tour,/auditLocalEvidence/);
  assert.match(tour,/No verification pass is claimed/);
  assert.match(tour,/does not prove training/);
  assert.doesNotMatch(tour,/innerHTML\s*=/);
});
