/** Independent, read-only consistency audit of public local GradientMine evidence.
 * Checks downloaded bytes, declared signers, and cross-artifact references.
 * It does NOT prove training, evaluation truth, absence of leakage, or Devnet settlement.
 * Never executes worker code or writes on-chain.
 */
import {sha256, verifyEnvelope, equal} from './core.mjs';

const SHA=/^[a-f0-9]{64}$/;
const expect=(ok,message)=>{if(!ok)throw Error(message);};
const checkSHA=(value,name)=>expect(typeof value==='string'&&SHA.test(value),'Invalid '+name+' commitment.');
const rawBytes=value=>{
  if(value instanceof Uint8Array)return value;
  if(value instanceof ArrayBuffer)return new Uint8Array(value);
  throw Error('Artifact source returned invalid bytes.');
};

export async function auditLocalEvidence(record,loadArtifact,onProgress=()=>{}) {
  const job=record?.job,policy=job?.policy,subs=job?.submissions;
  expect(record?.mode==='local'&&job?.mode==='local'&&job?.state==='EVALUATED',
    'Audit accepts the recorded evaluated local proof only.');
  expect(!job.funding_signature&&!job.settlement_signature&&!job.refund_signature,
    'Unexpected blockchain transaction in recorded local proof.');
  expect(policy&&typeof policy==='object'&&!Array.isArray(policy),
    'Recorded policy unavailable.');
  expect(Array.isArray(subs)&&subs.length>0&&subs.length<=16,
    'Invalid submission count.');
  checkSHA(job.policy_sha256,'policy');
  checkSHA(policy.parent_sha256,'parent');
  const referenced=new Set([job.policy_sha256,policy.parent_sha256]);
  for(const sub of subs){
    expect(typeof sub.worker==='string'&&sub.worker.length>12,'Invalid worker.');
    for(const key of ['artifact_sha256','manifest_sha256','model_sha256','receipt_sha256']){
      checkSHA(sub[key],key);
      referenced.add(sub[key]);
    }
  }
  expect(Array.isArray(record.artifacts)&&record.artifacts.length===referenced.size&&
    record.artifacts.length>=4&&record.artifacts.length<=80,
    'Public artifact allowlist has extra or missing hashes.');
  const supplied=new Set(record.artifacts);
  expect(supplied.size===referenced.size&&[...referenced].every(hash=>supplied.has(hash)),
    'Artifact allowlist differs from job commitments.');

  const values=new Map();
  let complete=0;
  for(const hash of supplied){
    checkSHA(hash,'artifact');
    const raw=rawBytes(await loadArtifact(hash));
    expect(raw.byteLength>0&&raw.byteLength<=262144,
      'Public artifact size exceeds expected limit.');
    expect(await sha256(raw)===hash,'Downloaded artifact SHA-256 does not match '+hash+'.');
    let value;
    try{value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw))}
    catch{throw Error('Malformed UTF-8/JSON artifact '+hash+'.')}
    values.set(hash,value);
    complete++;
    onProgress({completed:complete,total:supplied.size});
  }
  expect(equal(values.get(job.policy_sha256),policy),
    'Downloaded policy differs from the displayed frozen policy.');

  let signatures=0;
  for(const sub of subs){
    const manifest=values.get(sub.manifest_sha256);
    expect(await verifyEnvelope(manifest,sub.worker),
      'Worker manifest signature invalid for '+sub.id+'.');
    const mp=manifest.payload;
    expect(mp.format==='gradientmine.submission.v1'&&mp.job_id===job.id&&
      mp.parent_sha256===policy.parent_sha256&&
      mp.policy_sha256===job.policy_sha256&&
      mp.artifact_sha256===sub.artifact_sha256&&
      mp.training_data_sha256===policy.train_sha256,
      'Worker manifest has inconsistent bounty commitments.');
    signatures++;

    const receipt=values.get(sub.receipt_sha256);
    expect(await verifyEnvelope(receipt,policy.validator),
      'Evaluator receipt signature invalid for '+sub.id+'.');
    const rp=receipt.payload;
    expect(rp.format==='gradientmine.evaluation.v1'&&rp.job_id===job.id&&
      rp.worker===sub.worker&&rp.validator===policy.validator&&
      rp.policy_sha256===job.policy_sha256&&
      rp.parent_sha256===policy.parent_sha256&&
      rp.artifact_sha256===sub.artifact_sha256&&
      rp.manifest_sha256===sub.manifest_sha256&&
      rp.model_sha256===sub.model_sha256&&
      rp.evaluation_sha256===policy.evaluation_sha256&&
      Number.isFinite(rp.evaluated_at)&&rp.evaluated_at>=policy.deadline&&
      equal(rp.score,sub.score),
      'Signed evaluator receipt has inconsistent score, signer or lineage.');
    signatures++;
  }
  const winner=job.winner;
  expect(winner&&winner.eligible===true,'The local proof has no eligible selected winner.');
  const matched=subs.filter(sub=>sub.id===winner.submission_id);
  expect(matched.length===1,'Recorded winner does not match one submission.');
  const sub=matched[0];
  expect(sub.score?.eligible===true&&
    sub.artifact_sha256===winner.artifact_sha256&&
    sub.model_sha256===winner.model_sha256&&
    sub.receipt_sha256===winner.receipt_sha256&&sub.worker===winner.worker,
    'Winner differs from evaluated signed submission.');
  const better=subs.filter(s=>s.score?.eligible).some(s=>
    s.score.candidate_accuracy>sub.score.candidate_accuracy+1e-12);
  expect(!better,'Recorded winner is below another eligible candidate.');

  return {
    status:'verified-public-evidence',
    artifactsVerified:complete,
    signaturesVerified:signatures,
    policyMatches:true,
    winnerReferencesMatch:true,
    proofOfTraining:false,
    provedModelQuality:false,
    devnetPayment:false,
    scope:'Downloaded artifact hashes, expected Ed25519 signers, policy and winner references ONLY.',
  };
}
