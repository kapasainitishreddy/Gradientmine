import test from 'node:test';
import assert from 'node:assert/strict';
import {
  assuranceContract,
  artifactFirewall,
  arenaCandidates,
  modelPassport,
} from '../../web/assets/assurance.mjs';

const job = {
  id: 'job-1',
  mode: 'local',
  state: 'EVALUATED',
  policy_sha256: '1'.repeat(64),
  settlement_signature: null,
  baseline_accuracy: 0.8472222222,
  policy: {
    task: 'digits-lora-v1',
    metric: 'accuracy',
    minimum_delta: 0.01,
    familywise_alpha: 0.05,
    max_candidates: 8,
    bootstrap_resamples: 20000,
    statistical_rule: 'paired-multinomial-bootstrap-v1',
    evaluation_sha256: '2'.repeat(64),
    parent_sha256: '3'.repeat(64),
    validator: 'validator-address',
    benchmark_warning: 'Public benchmark is reconstructible.',
  },
  submissions: [
    {
      id: 'sub-a',
      worker: 'worker-a',
      artifact_sha256: '4'.repeat(64),
      manifest_sha256: '5'.repeat(64),
      model_sha256: '6'.repeat(64),
      receipt_sha256: '7'.repeat(64),
      worker_metrics: {public_validation_accuracy: 0.9275, elapsed_seconds: 1.5, negative_control: false},
      score: {candidate_accuracy: 0.9528, delta: 0.1056, bootstrap_lower_bound: 0.0611, n: 360, eligible: true},
      state: 'ELIGIBLE',
    },
    {
      id: 'sub-b',
      worker: 'worker-b',
      artifact_sha256: '8'.repeat(64),
      manifest_sha256: '9'.repeat(64),
      model_sha256: 'a'.repeat(64),
      receipt_sha256: 'b'.repeat(64),
      worker_metrics: {public_validation_accuracy: 0.24, elapsed_seconds: 2.6, negative_control: true},
      score: {candidate_accuracy: 0.25, delta: -0.5972, bootstrap_lower_bound: -0.66, n: 360, eligible: false},
      state: 'REJECTED',
    },
  ],
  winner: {
    submission_id: 'sub-a',
    worker: 'worker-a',
    artifact_sha256: '4'.repeat(64),
    model_sha256: '6'.repeat(64),
    receipt_sha256: '7'.repeat(64),
    candidate_accuracy: 0.9528,
    delta: 0.1056,
    bootstrap_lower_bound: 0.0611,
    n: 360,
  },
};

test('assurance contract exposes committed objective, budget and trust boundary', () => {
  const c = assuranceContract(job);
  assert.equal(c.metric, 'accuracy');
  assert.equal(c.minimum_delta, 0.01);
  assert.equal(c.familywise_confidence, 0.95);
  assert.equal(c.max_candidates, 8);
  assert.equal(c.bootstrap_resamples, 20000);
  assert.equal(c.evaluator, 'validator-address');
  assert.equal(c.evaluation_commitment, '2'.repeat(64));
  assert.match(c.trust_boundary, /named evaluator/i);
});

test('arena keeps worker development score separate from assurance evaluation', () => {
  const rows = arenaCandidates(job);
  assert.equal(rows[0].development_score, 0.9275);
  assert.equal(rows[0].assurance_score, 0.9528);
  assert.equal(rows[0].winner, true);
  assert.equal(rows[1].negative_control, true);
  assert.equal(rows[1].eligible, false);
  assert.equal(rows[0].runtime_efficiency_pp_per_second > 0, true);
});

test('artifact firewall describes admission controls without claiming malware proof', () => {
  const f = artifactFirewall(job.submissions[0]);
  assert.equal(f.content_addressed, true);
  assert.equal(f.signed_manifest_present, true);
  assert.equal(f.executable_payload_allowed, false);
  assert.equal(f.protocol_format, 'bounded numeric JSON adapter');
  assert.match(f.limit, /not.*backdoor/i);
});

test('model passport records provenance and refuses to invent a local payout', () => {
  const p = modelPassport(job);
  assert.equal(p.format, 'gradientmine.model-passport.v1');
  assert.equal(p.parent_sha256, '3'.repeat(64));
  assert.equal(p.model_sha256, '6'.repeat(64));
  assert.equal(p.worker, 'worker-a');
  assert.equal(p.validator, 'validator-address');
  assert.equal(p.observed_delta, 0.1056);
  assert.equal(p.lower_bound, 0.0611);
  assert.equal(p.paid, false);
  assert.equal(p.settlement_signature, null);
  assert.match(p.assurance_level, /named evaluator/i);
});

test('passport handles an inconclusive/no-winner bounty without fabricating a model', () => {
  const p = modelPassport({...job, winner: null, state: 'NO_WINNER'});
  assert.equal(p.model_sha256, null);
  assert.equal(p.worker, null);
  assert.equal(p.paid, false);
});
