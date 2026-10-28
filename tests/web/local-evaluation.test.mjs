import test from 'node:test';
import assert from 'node:assert/strict';
import {
  freezePolicy,createSyntheticSubmission,inspectSubmission,evaluateSubmission,
  verifyEvaluationReceipt,validateCandidateShape,beginSettlementRecoveryDrill,
  reconcileSettlementRecoveryDrill,validateSettlementRecoveryDrill,baselineSha256,heldoutSize,canonicalJSON,sha256,
} from '../../web/assets/local-evaluation.mjs';

const raw={name:'Synthetic routing improvement',model:'local-toy-model-v1',metric:'accuracy',baseline:'50',target:'60',reward:'2',durationDays:'14',candidates:'2',evaluator:'Local demo evaluator',rights:true};

test('freezes a canonical immutable policy with lineage, budget, evaluator and visible synthetic limits',async()=>{
  const policy=await freezePolicy(raw,'2026-10-28T12:00:00.000Z');
  assert.equal(policy.status,'FROZEN_LOCAL_UNFUNDED_SIMULATION');
  assert.equal(policy.parent.sha256,baselineSha256());
  assert.equal(policy.objective.minimum_delta,.1);
  assert.equal(policy.candidate_budget,2);
  assert.equal(policy.local_fixture_candidate_capacity,1);
  assert.equal(policy.tie_break,'artifact_sha256_ascending');
  assert.equal(policy.heldout.examples,heldoutSize());
  assert.match(policy.evaluator.trust_boundary,/One local JavaScript evaluator is trusted/i);
  assert.match(policy.statistical_limit,/No statistical confidence claim/);
  await assert.rejects(freezePolicy({...raw,metric:'retrieval'}),/accuracy task only/);
  await assert.rejects(freezePolicy({...raw,candidates:'9'}),/1–8/);
});

test('admission checks LoRA shape, baseline/policy binding, hash, signature, replay and duplicate',async()=>{
  const policy=await freezePolicy(raw,'2026-10-28T12:00:00.000Z');
  const submission=await createSyntheticSubmission(policy);
  const valid=await inspectSubmission(submission,policy,[]);
  assert.equal(valid.admitted,true);
  assert.deepEqual(valid.checks.map(x=>x.ok),[true,true,true,true,true]);
  const duplicate=await inspectSubmission(submission,policy,[submission]);
  assert.equal(duplicate.admitted,false);
  assert.match(duplicate.checks.find(x=>x.name==='Replay / duplicate').detail,/already been admitted/);
  const wrongShape=structuredClone(submission);wrongShape.artifact.A[0]=[1,2];
  const shapeResult=await inspectSubmission(wrongShape,policy,[]);
  assert.equal(shapeResult.admitted,false);
  assert.equal(shapeResult.checks.find(x=>x.name==='Candidate shape').ok,false);
  assert.equal(shapeResult.checks.find(x=>x.name==='Artifact hash').ok,false);
  const badSignature=structuredClone(submission);badSignature.worker_signature=submission.worker_signature.slice(0,-2)+'AA';
  const signatureResult=await inspectSubmission(badSignature,policy,[]);
  assert.equal(signatureResult.admitted,false);
  assert.equal(signatureResult.checks.find(x=>x.name==='Worker signature').ok,false);
  const wrongParent=structuredClone(submission);wrongParent.artifact.baseline_sha256='0'.repeat(64);
  assert.ok(validateCandidateShape(wrongParent.artifact,policy).some(x=>/baseline hash/.test(x)));
  const executableField=structuredClone(submission);executableField.artifact.execute='ignored';
  assert.ok(validateCandidateShape(executableField.artifact,policy).some(x=>/fixed adapter schema/.test(x)));
  const nonFinite=structuredClone(submission);nonFinite.artifact.A[0][0]=Number.NaN;
  assert.ok(validateCandidateShape(nonFinite.artifact,policy).some(x=>/non-finite/.test(x)));
  const replay=structuredClone(submission);replay.submission_id='different-id';
  assert.equal((await inspectSubmission(replay,policy,[submission])).admitted,false);
});

test('held-out synthetic scoring produces a signed, lineage-bound unfunded receipt',async()=>{
  const policy=await freezePolicy(raw,'2026-10-28T12:00:00.000Z');
  const submission=await createSyntheticSubmission(policy);
  const envelope=await evaluateSubmission(submission,policy,[]);
  assert.equal(envelope.receipt.status,'SIMULATED_SYNTHETIC_EVALUATION');
  assert.equal(envelope.receipt.baseline_accuracy,.5);
  assert.equal(envelope.receipt.candidate_accuracy,1);
  assert.equal(envelope.receipt.observed_delta,.5);
  assert.equal(envelope.receipt.eligible,true);
  assert.equal(envelope.receipt.parent_sha256,policy.parent.sha256);
  assert.equal(envelope.receipt.candidate_artifact_sha256,submission.artifact_sha256);
  assert.equal(envelope.receipt.candidate_budget,2);
  assert.equal(envelope.receipt.local_fixture_candidate_capacity,1);
  assert.equal(envelope.receipt.candidates_evaluated,1);
  assert.equal(envelope.receipt.tie_break,'artifact_sha256_ascending');
  assert.equal(envelope.receipt.tie_break_applied,false);
  assert.equal(envelope.receipt.selection_method,'single_candidate_fixture_no_ranking');
  assert.equal(envelope.receipt.funds_escrowed,false);
  assert.equal(envelope.receipt.transaction_signature,null);
  assert.equal(envelope.receipt.payout_count,0);
  assert.equal((await verifyEvaluationReceipt(envelope,policy,submission)).ok,true);
  const tampered=structuredClone(envelope);tampered.receipt.candidate_accuracy=.25;
  assert.equal((await verifyEvaluationReceipt(tampered,policy,submission)).ok,false);
  const lied=structuredClone(envelope);lied.receipt.settlement_status='SETTLED';
  assert.equal((await verifyEvaluationReceipt(lied,policy,submission)).ok,false);
  const misleadingSelection=structuredClone(envelope);misleadingSelection.receipt.tie_break_applied=true;
  assert.equal((await verifyEvaluationReceipt(misleadingSelection,policy,submission)).ok,false);
  const attackerPolicy=structuredClone(policy);attackerPolicy.evaluator.public_key='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=';
  delete attackerPolicy.policy_sha256;attackerPolicy.policy_sha256=await sha256(canonicalJSON(attackerPolicy));
  const attackerEnvelope=structuredClone(envelope);attackerEnvelope.receipt.policy_sha256=attackerPolicy.policy_sha256;
  attackerEnvelope.receipt_sha256=await sha256(canonicalJSON(attackerEnvelope.receipt));
  assert.equal((await verifyEvaluationReceipt(attackerEnvelope,attackerPolicy,submission)).ok,false);
});

test('cancellation/checkpoint recovery and ambiguous settlement reconciliation cannot pay twice',()=>{
  let state={policy:{policy_sha256:'a'.repeat(64)},submissions:[{id:'s1'}],receipt:{}};
  const interrupted=structuredClone(state);
  const resumed=structuredClone(interrupted);
  assert.deepEqual(resumed,interrupted);
  let drill=beginSettlementRecoveryDrill(resumed);
  assert.equal(drill.settlement_probe.transaction_sent,false);
  assert.equal(drill.settlement_probe.payout_count,0);
  assert.throws(()=>validateSettlementRecoveryDrill({...drill.settlement_probe,payout_count:1}),/cannot report a payment/);
  assert.equal(drill.settlement_probe.transaction_signature,null);
  drill=reconcileSettlementRecoveryDrill(drill);
  drill=reconcileSettlementRecoveryDrill(drill);
  assert.equal(drill.settlement_probe.status,'RECONCILED_NO_TRANSACTION');
  assert.equal(drill.settlement_probe.recovery_checks,2);
  assert.equal(drill.settlement_probe.payout_count,0);
  state={cancelled:true,policy:null,submissions:[],receipt:null};
  assert.equal(state.policy,null);
});
