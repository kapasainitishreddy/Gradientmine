/**
 * GradientMine buyer-side bounty blueprint. A client-only planning tool.
 * It does NOT create a job, upload a model, freeze an assurance set,
 * reserve wallet funds, deploy a chain program, or collect fees.
 */
export const METRICS = Object.freeze({
  accuracy: {label: 'Classification accuracy', unit: '%', direction: 'higher', min: 0, max: 100, supported: 'Verified Digits prototype'},
  retrieval: {label: 'Retrieval recall@k', unit: '%', direction: 'higher', min: 0, max: 100, supported: 'Research Lab prototype'},
  latency: {label: 'P95 latency', unit: 'ms', direction: 'lower', min: 0.001, max: 1000000, supported: 'Proposed production task'},
  cost: {label: 'Inference cost per 1k requests', unit: 'USD', direction: 'lower', min: 0.000001, max: 1000000, supported: 'Proposed production task'},
});
export const FEE_RATE = 0.10; // Hypothetical business model, not a real fee.
export const DEMO_BLUEPRINT = Object.freeze({
  name: 'Support routing accuracy fix (illustrative)',
  model: 'support-router-v7 (example, not a GradientMine deployment)',
  metric: 'accuracy', baseline: '84', target: '92', reward: '2',
  evaluator: 'Proposed independent evaluator (illustrative)',
  durationDays: '14', candidates: '8', candidateResult: '95', rights: true,
});

const number = input => {
  if (input === '' || input == null || String(input).trim() === '') return NaN;
  const value = Number(input);
  return Number.isFinite(value) ? value : NaN;
};
const clean = (value, limit) => String(value ?? '').trim().slice(0, limit);
const round = value => Math.round((value + Number.EPSILON) * 1e6) / 1e6;
const safe = (value, min, max) => Number.isFinite(value) && value >= min && value <= max;

export function analyzeBlueprint(raw = {}) {
  const spec = METRICS[raw.metric] || null;
  const baseline = number(raw.baseline);
  const target = number(raw.target);
  const reward = number(raw.reward);
  const durationDays = number(raw.durationDays);
  const candidates = number(raw.candidates);
  const name = clean(raw.name, 100);
  const model = clean(raw.model, 160);
  const evaluator = clean(raw.evaluator, 100);
  const issues = [];
  if (name.length < 6) issues.push('Give the model problem a descriptive title (6+ characters).');
  if (model.length < 3) issues.push('Identify the frozen parent model or checkpoint (3+ characters).');
  if (!spec) issues.push('Choose a supported planning metric.');
  if (spec && !safe(baseline, spec.min, spec.max)) issues.push('Baseline must be between '+spec.min+' and '+spec.max+' '+spec.unit+'.');
  if (spec && !safe(target, spec.min, spec.max)) issues.push('Target must be between '+spec.min+' and '+spec.max+' '+spec.unit+'.');
  const direction = spec?.direction;
  if (spec && safe(baseline,spec.min,spec.max) && safe(target,spec.min,spec.max) &&
    (direction === 'higher' ? target <= baseline : target >= baseline)) {
    issues.push('Target must improve on the baseline in the metric direction.');
  }
  if (!safe(reward, 0.001, 1000)) issues.push('Illustrative reward must be 0.001–1000 SOL.');
  if (!Number.isInteger(durationDays) || durationDays < 1 || durationDays > 90)
    issues.push('Choose a contest window of 1–90 whole days.');
  if (!Number.isInteger(candidates) || candidates < 1 || candidates > 32)
    issues.push('Candidate budget must be a whole number from 1–32.');
  if (evaluator.length < 8) issues.push('Name a proposed evaluator or evaluation authority (8+ characters).');
  if (raw.rights !== true) issues.push('Confirm model/data rights before exporting an evaluation blueprint.');

  const validMetrics = spec && safe(baseline,spec.min,spec.max) && safe(target,spec.min,spec.max);
  const delta = validMetrics ? (direction === 'higher' ? target - baseline : baseline - target) : null;
  const sample = number(raw.candidateResult);
  const sampleWithinRange = !!spec && safe(sample, spec.min, spec.max);
  const arithmeticPass = issues.length === 0 && sampleWithinRange
    ? (direction === 'higher' ? sample >= target : sample <= target) : null;
  const plannedFee = safe(reward,0.001,1000) ? round(reward * FEE_RATE) : null;
  return {
    ready: issues.length === 0, issues,
    label: name, model, metric: raw.metric, spec,
    baseline: Number.isFinite(baseline) ? baseline : null,
    target: Number.isFinite(target) ? target : null,
    delta: delta == null ? null : round(delta),
    reward: Number.isFinite(reward) ? reward : null,
    durationDays, candidates, evaluator,
    plannedFee, illustrativeTotal: plannedFee == null ? null : round(reward + plannedFee),
    candidateResult: sampleWithinRange ? sample : null,
    arithmeticPass,
    tested: false, funded: false, verified: false,
  };
}

export function draftArtifact(raw, createdAt = new Date().toISOString()) {
  const analysis = analyzeBlueprint(raw);
  if (!analysis.ready) throw new Error('Complete all validation checks before exporting a blueprint.');
  return {
    format: 'gradientmine.bounty-blueprint.v1', created_at: createdAt,
    status: 'UNFUNDED_DESIGN_DRAFT',
    title: analysis.label, parent_model: analysis.model,
    objective: {
      metric: analysis.metric, metric_label: analysis.spec.label,
      direction: analysis.spec.direction, unit: analysis.spec.unit,
      measured_baseline_provided_by_user: analysis.baseline,
      improvement_target_provided_by_user: analysis.target,
      minimum_delta_proposed: analysis.delta,
      actual_holdout_evaluation: 'NOT_CONFIGURED',
    },
    evaluation: {
      proposed_evaluator: analysis.evaluator,
      deadline_in_days: analysis.durationDays, candidate_budget: analysis.candidates,
      benchmark_status: 'NOT_UPLOADED_OR_VERIFIED',
      evaluation_method: 'Must be agreed, licensed, sealed and independently run.',
      statistical_eligibility: 'Not computed; threshold alone does not establish winner eligibility.',
      parent_and_dataset_hashes: 'NOT_COMMITTED',
    },
    economics: {
      illustrative_solver_reward_sol: analysis.reward,
      hypothetical_fee_rate: FEE_RATE,
      hypothetical_fee_sol: analysis.plannedFee,
      hypothetical_total_owner_budget_sol: analysis.illustrativeTotal,
      charge_model_assumption: 'Fee charged on top of solver reward, if the planned 10% fee is adopted.',
      current_billing_status: 'NOT_IMPLEMENTED',
      wallet_connected: false, funds_escrowed: false, settlement_signature: null,
    },
    implementation_boundary: {
      exported_locally_only: true, not_an_onchain_bounty: true,
      not_a_worker_submitted_artifact: true, not_a_live_model_evaluation: true,
      broader_task_types_may_require_future_backend_work: true,
    },
  };
}

export function candidateLabel(analysis) {
  if (!analysis.ready) return 'Complete the bounty rules to inspect hypothetical eligibility.';
  if (analysis.candidateResult == null) return 'Enter a hypothetical candidate metric to compare with the target.';
  return analysis.arithmeticPass
    ? 'Passes the numeric target ONLY. Still needs held-out evaluation, statistical checks, artifact admission and signer approval.'
    : 'Misses the frozen target. This would not clear the numeric improvement requirement.';
}
