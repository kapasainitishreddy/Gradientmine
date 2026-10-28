/**
 * Offline, synthetic buyer-journey demonstration. This is deliberately not a
 * model service, wallet integration, or private evaluation environment.
 */
import {draftArtifact} from './bounty-blueprint.mjs';

const encoder = new TextEncoder();
const HOLDOUT = Object.freeze(Array.from({length:16},(_,i)=>{
  const positive = i % 2 === 1;
  return {x:[positive?1:-1,(i%4)/10,((i*3)%7)/10,((i*5)%9)/10], y:positive?1:0};
}));
const BASELINE_SHA256 = '2f625a3fcffd39a2c184ef30ed587bcee43646ff5ef14f84c383b092ccddcf1f';
const BASELINE_MODEL=Object.freeze({format:'gradientmine.synthetic-baseline.v1',input_dim:4,output_dim:2,weights:[[0,0],[0,0],[0,0],[0,0]]});
const STAT_LIMIT = 'Synthetic 16-example sanity check only. No statistical confidence claim, benchmark secrecy, training proof, or generalization guarantee.';
const EVALUATOR_LIMIT = 'One local JavaScript evaluator is trusted for this simulation. The frozen policy pins a public test key whose private half is bundled in this public demo source; signature verification detects accidental edits only and does not establish evaluator identity, independent or trustless evaluation.';
const SYNTHETIC_EVALUATOR_PRIVATE_PKCS8='MC4CAQAwBQYDK2VwBCIEIAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8g';
const SYNTHETIC_EVALUATOR_PUBLIC_RAW='ebVWLo/mVPlAeLES6KmLp5AfhTrmlb7X4OORC60ElmQ=';
const isObject = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const finiteTree = value => typeof value === 'number' ? Number.isFinite(value) : Array.isArray(value) ? value.every(finiteTree) : isObject(value) ? Object.values(value).every(finiteTree) : true;

export function canonicalJSON(value) {
  if (Array.isArray(value)) return '['+value.map(canonicalJSON).join(',')+']';
  if (isObject(value)) return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonicalJSON(value[k])).join(',')+'}';
  return JSON.stringify(value);
}

export async function sha256(value) {
  const bytes = typeof value === 'string' ? encoder.encode(value) : value;
  const digest = await crypto.subtle.digest('SHA-256',bytes);
  return [...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('');
}

export async function freezePolicy(raw,createdAt=new Date().toISOString()) {
  if (raw.metric !== 'accuracy') throw new Error('The local escrow-path simulation supports the Digits accuracy task only. Other Research Lab task types stay separate.');
  if (!Number.isInteger(Number(raw.candidates)) || Number(raw.candidates) < 1 || Number(raw.candidates) > 8)
    throw new Error('The Digits escrow candidate budget must be 1–8.');
  const draft=draftArtifact({...raw,rights:true},createdAt);
  if(await sha256(canonicalJSON(BASELINE_MODEL))!==BASELINE_SHA256)throw new Error('Synthetic baseline bytes do not match their committed hash.');
  const policy={
    format:'gradientmine.local-synthetic-policy.v1',
    status:'FROZEN_LOCAL_UNFUNDED_SIMULATION',
    source_draft:draft,
    parent:{model_id:'synthetic-toy-baseline-v1',sha256:BASELINE_SHA256,lineage:'Fixed zero-weight 4-feature, 2-class model; SHA-256 is over its canonical model bytes; unrelated to any uploaded or customer model.'},
    objective:{metric:'accuracy',direction:'higher',minimum_delta:(Number(raw.target)-Number(raw.baseline))/100,unit:'fraction',target_origin:'User-authored planning draft; target checked separately from synthetic holdout.'},
    evaluator:{name:'Local Synthetic Evaluator',authority:'single trusted browser module',public_key:SYNTHETIC_EVALUATOR_PUBLIC_RAW,public_key_sha256:await sha256(fromB64(SYNTHETIC_EVALUATOR_PUBLIC_RAW)),trust_boundary:EVALUATOR_LIMIT},
    candidate_budget:Number(raw.candidates),
    local_fixture_candidate_capacity:1,
    tie_break:'artifact_sha256_ascending',
    artifact_policy:{format:'gradientmine.synthetic-lora.v1',input_dim:4,output_dim:2,rank:1,executable_code:false,absolute_value_max:4},
    heldout:{name:'source-bundled synthetic fixture',examples:HOLDOUT.length,secret:false,sha256:await sha256(canonicalJSON(HOLDOUT)),disclosure:'Visible/reconstructible synthetic fixture; not a privacy or anti-leakage boundary.'},
    statistical_limit:STAT_LIMIT,
    settlement:{mode:'UNFUNDED_LOCAL_ONLY',funds_escrowed:false,transaction_signature:null,payout_count:0},
    frozen_at:createdAt,
  };
  policy.policy_sha256=await sha256(canonicalJSON(policy));
  return policy;
}

export function syntheticCandidate(policySha256) {
  return {
    format:'gradientmine.synthetic-lora.v1',
    policy_sha256:policySha256,
    baseline_sha256:BASELINE_SHA256,
    rank:1,input_dim:4,output_dim:2,
    A:[[1],[0],[0],[0]],
    B:[[-1,1]],
    lineage:'Synthetic adapter delta applied to the frozen synthetic baseline; not trained weights.',
  };
}

export function validateCandidateShape(candidate,policy) {
  const errors=[];
  if (!isObject(candidate)) return ['Candidate must be a JSON object.'];
  if (candidate.format!=='gradientmine.synthetic-lora.v1') errors.push('Unsupported candidate format.');
  const allowed=new Set(['format','policy_sha256','baseline_sha256','rank','input_dim','output_dim','A','B','lineage']);
  if (Object.keys(candidate).some(key=>!allowed.has(key))) errors.push('Candidate contains fields outside the fixed adapter schema.');
  if (candidate.policy_sha256!==policy?.policy_sha256) errors.push('Candidate is bound to a different frozen policy.');
  if (candidate.baseline_sha256!==BASELINE_SHA256) errors.push('Candidate parent/baseline hash does not match frozen lineage.');
  if (candidate.rank!==1||candidate.input_dim!==4||candidate.output_dim!==2) errors.push('Candidate shape must be rank-1, 4-input, 2-output.');
  if (!Array.isArray(candidate.A)||candidate.A.length!==4||candidate.A.some(row=>!Array.isArray(row)||row.length!==1)) errors.push('Adapter A must have shape [4,1].');
  if (!Array.isArray(candidate.B)||candidate.B.length!==1||candidate.B.some(row=>!Array.isArray(row)||row.length!==2)) errors.push('Adapter B must have shape [1,2].');
  if (!finiteTree(candidate)) errors.push('Candidate contains non-finite numeric values.');
  const values=[...(candidate.A||[]).flat(),...(candidate.B||[]).flat()];
  if (values.some(x=>typeof x!=='number'||Math.abs(x)>4)) errors.push('Adapter values must be finite numbers in [-4,4].');
  return [...new Set(errors)];
}

const b64 = bytes => btoa(String.fromCharCode(...new Uint8Array(bytes)));
const fromB64 = value => Uint8Array.from(atob(value),c=>c.charCodeAt(0));
const importPublic = value => crypto.subtle.importKey('raw',fromB64(value),{name:'Ed25519'},false,['verify']);
const signedBytes = (artifactSha,policySha,submissionId) => encoder.encode(canonicalJSON({artifact_sha256:artifactSha,policy_sha256:policySha,submission_id:submissionId}));

export async function createSyntheticSubmission(policy,submissionId='local-candidate-1') {
  const candidate=syntheticCandidate(policy.policy_sha256);
  const artifactSha=await sha256(canonicalJSON(candidate));
  const pair=await crypto.subtle.generateKey({name:'Ed25519'},true,['sign','verify']);
  const publicKey=b64(await crypto.subtle.exportKey('raw',pair.publicKey));
  const signature=b64(await crypto.subtle.sign('Ed25519',pair.privateKey,signedBytes(artifactSha,policy.policy_sha256,submissionId)));
  return {submission_id:submissionId,artifact:candidate,artifact_sha256:artifactSha,worker_public_key:publicKey,worker_signature:signature,fixture_label:'synthetic browser-generated signer; not a wallet or real worker identity'};
}

export async function inspectSubmission(submission,policy,existing=[]) {
  const submitted=isObject(submission)?submission:{};
  const checks=[];
  const candidate=submitted.artifact;
  const artifactSha=isObject(candidate)?await sha256(canonicalJSON(candidate)):null;
  const identityOk=typeof submitted.submission_id==='string'&&submitted.submission_id.length>0&&submitted.submission_id.length<=128;
  checks.push({name:'Submission identity',ok:identityOk,detail:identityOk?'Submission ID is bounded and present.':'Submission ID is missing or exceeds 128 characters.'});
  checks.push({name:'Candidate shape',ok:validateCandidateShape(candidate,policy).length===0,detail:validateCandidateShape(candidate,policy).join(' ')||'Rank/dimensions, parent, policy binding and numeric bounds match.'});
  checks.push({name:'Artifact hash',ok:artifactSha===submission?.artifact_sha256,detail:artifactSha===submission?.artifact_sha256?'Canonical candidate bytes match the declared SHA-256.':'Candidate bytes differ from the signed SHA-256.'});
  let signatureOk=false;
  try {
    signatureOk=await crypto.subtle.verify('Ed25519',await importPublic(submitted.worker_public_key),fromB64(submitted.worker_signature),signedBytes(submitted.artifact_sha256,policy.policy_sha256,submitted.submission_id));
  } catch { signatureOk=false; }
  checks.push({name:'Worker signature',ok:signatureOk,detail:signatureOk?'Synthetic Ed25519 key signs the candidate hash and frozen policy.':'Signature is missing, malformed, or does not bind this candidate and policy.'});
  const duplicate=existing.some(row=>row.submission_id===submitted.submission_id||row.artifact_sha256===artifactSha);
  checks.push({name:'Replay / duplicate',ok:!duplicate,detail:duplicate?'Submission ID or exact artifact has already been admitted.':'No prior submission has this ID or exact artifact hash.'});
  return {admitted:checks.every(x=>x.ok),artifact_sha256:artifactSha,checks};
}

function predict(candidate,x) {
  const z=candidate.A.reduce((sum,row,i)=>sum+x[i]*row[0],0);
  const logits=candidate.B[0].map(v=>z*v);
  return logits[1]>logits[0]?1:0;
}

export async function evaluateSubmission(submission,policy,existing=[]) {
  const admission=await inspectSubmission(submission,policy,existing);
  if (!admission.admitted) throw new Error('Candidate admission failed; evaluation was not run.');
  const baselineCorrect=HOLDOUT.reduce((n,row)=>n+(0===row.y?1:0),0);
  const candidateCorrect=HOLDOUT.reduce((n,row)=>n+(predict(submission.artifact,row.x)===row.y?1:0),0);
  const baseline=baselineCorrect/HOLDOUT.length,score=candidateCorrect/HOLDOUT.length,delta=score-baseline;
  const receipt={
    format:'gradientmine.synthetic-evaluation-receipt.v1',
    status:'SIMULATED_SYNTHETIC_EVALUATION',
    policy_sha256:policy.policy_sha256,
    parent_sha256:policy.parent.sha256,
    candidate_artifact_sha256:submission.artifact_sha256,
    candidate_model_sha256:await sha256(canonicalJSON({parent:policy.parent.sha256,adapter:submission.artifact})),
    metric:'accuracy',baseline_accuracy:baseline,candidate_accuracy:score,observed_delta:delta,
    minimum_delta:policy.objective.minimum_delta,eligible:delta>=policy.objective.minimum_delta,
    candidate_budget:policy.candidate_budget,local_fixture_candidate_capacity:policy.local_fixture_candidate_capacity,
    tie_break:policy.tie_break,tie_break_applied:false,selection_method:'single_candidate_fixture_no_ranking',
    candidates_evaluated:1,evaluation_examples:HOLDOUT.length,
    statistical_limit:STAT_LIMIT,evaluator_trust_boundary:EVALUATOR_LIMIT,
    settlement_status:'UNFUNDED_SIMULATION_ONLY',funds_escrowed:false,transaction_signature:null,payout_count:0,
  };
  const evaluatorPrivateKey=await crypto.subtle.importKey('pkcs8',fromB64(SYNTHETIC_EVALUATOR_PRIVATE_PKCS8),{name:'Ed25519'},false,['sign']);
  const receiptSha=await sha256(canonicalJSON(receipt));
  const evaluatorSignature=b64(await crypto.subtle.sign('Ed25519',evaluatorPrivateKey,encoder.encode(receiptSha)));
  return {receipt,receipt_sha256:receiptSha,evaluator_signature:evaluatorSignature};
}

export async function verifyEvaluationReceipt(envelope,policy,submission) {
  if (!isObject(envelope?.receipt)) return {ok:false,reason:'Receipt is missing.'};
  const r=envelope.receipt;
  const receiptSha=await sha256(canonicalJSON(r));
  if (r.policy_sha256!==policy.policy_sha256||r.parent_sha256!==policy.parent.sha256||r.candidate_artifact_sha256!==submission.artifact_sha256)
    return {ok:false,reason:'Receipt lineage does not match frozen policy and admitted candidate.'};
  if (receiptSha!==envelope.receipt_sha256) return {ok:false,reason:'Receipt bytes do not match the signed hash.'};
  if (policy.evaluator?.public_key!==SYNTHETIC_EVALUATOR_PUBLIC_RAW
    ||await sha256(fromB64(policy.evaluator.public_key))!==policy.evaluator.public_key_sha256)
    return {ok:false,reason:'Frozen evaluator key does not match the bundled synthetic test key.'};
  if (policy.local_fixture_candidate_capacity!==1
    ||r.local_fixture_candidate_capacity!==1
    ||r.candidates_evaluated!==1
    ||r.candidate_budget!==policy.candidate_budget
    ||r.tie_break!==policy.tie_break
    ||r.tie_break_applied!==false
    ||r.selection_method!=='single_candidate_fixture_no_ranking')
    return {ok:false,reason:'Receipt does not match the one-candidate local fixture capacity and non-ranking disclosure.'};
  if (r.funds_escrowed!==false||r.transaction_signature!==null||r.payout_count!==0||r.settlement_status!=='UNFUNDED_SIMULATION_ONLY')
    return {ok:false,reason:'Synthetic receipt contains an unsupported settlement claim.'};
  try {
    const key=await importPublic(policy.evaluator.public_key);
    const ok=await crypto.subtle.verify('Ed25519',key,fromB64(envelope.evaluator_signature),encoder.encode(receiptSha));
    return ok?{ok:true,reason:'Synthetic evaluator signature and receipt lineage verified; evaluator remains trusted.'}:{ok:false,reason:'Evaluator signature verification failed.'};
  } catch { return {ok:false,reason:'Evaluator signature is malformed.'}; }
}

export function beginSettlementRecoveryDrill(checkpoint) {
  if (checkpoint.settlement_probe) {
    validateSettlementRecoveryDrill(checkpoint.settlement_probe);
    return checkpoint;
  }
  return {...checkpoint,settlement_probe:{status:'SIMULATED_RESPONSE_LOST',transaction_sent:false,transaction_signature:null,payout_count:0,recovery_checks:0}};
}

export function validateSettlementRecoveryDrill(probe) {
  const valid=isObject(probe)
    && ['SIMULATED_RESPONSE_LOST','RECONCILED_NO_TRANSACTION'].includes(probe.status)
    && probe.transaction_sent===false
    && probe.transaction_signature===null
    && probe.payout_count===0
    && Number.isInteger(probe.recovery_checks)
    && probe.recovery_checks>=0;
  if(!valid)throw new Error('Settlement drill checkpoint is malformed; it cannot report a payment or be recovered.');
  return true;
}

export function reconcileSettlementRecoveryDrill(checkpoint) {
  const probe=checkpoint.settlement_probe;
  if (!probe) throw new Error('No simulated ambiguous response exists to reconcile.');
  validateSettlementRecoveryDrill(probe);
  return {...checkpoint,settlement_probe:{...probe,status:'RECONCILED_NO_TRANSACTION',transaction_sent:false,transaction_signature:null,payout_count:0,recovery_checks:probe.recovery_checks+1}};
}

export function heldoutSize(){return HOLDOUT.length;}
export function baselineSha256(){return BASELINE_SHA256;}
