const sha = value => typeof value === 'string' && /^[a-f0-9]{64}$/i.test(value);
const finite = value => typeof value === 'number' && Number.isFinite(value);

export function assuranceContract(job) {
  const policy = job?.policy || {};
  const alpha = finite(policy.familywise_alpha) ? policy.familywise_alpha : null;
  return {
    format: 'gradientmine.assurance-contract.v1',
    metric: policy.metric || null,
    minimum_delta: finite(policy.minimum_delta) ? policy.minimum_delta : null,
    evaluator: policy.validator || null,
    evaluation_commitment: policy.evaluation_sha256 || null,
    statistical_rule: policy.statistical_rule || null,
    familywise_alpha: alpha,
    familywise_confidence: alpha == null ? null : 1 - alpha,
    max_candidates: Number.isInteger(policy.max_candidates) ? policy.max_candidates : null,
    bootstrap_resamples: Number.isInteger(policy.bootstrap_resamples) ? policy.bootstrap_resamples : null,
    benchmark_warning: policy.benchmark_warning || null,
    artifact_policy: 'bounded numeric adapter against a known architecture',
    trust_boundary: 'One named evaluator measures held-out quality and authorizes payout; this is not decentralized or cryptographic verification of training.',
  };
}

export function arenaCandidates(job) {
  const winnerId = job?.winner?.submission_id || null;
  return (job?.submissions || []).map(sub => {
    const elapsed = sub?.worker_metrics?.elapsed_seconds;
    const scoreDelta = sub?.score?.delta;
    return {
      submission_id: sub.id || null,
      worker: sub.worker || null,
      development_score: finite(sub?.worker_metrics?.public_validation_accuracy) ? sub.worker_metrics.public_validation_accuracy : null,
      assurance_score: finite(sub?.score?.candidate_accuracy) ? sub.score.candidate_accuracy : null,
      delta: finite(scoreDelta) ? scoreDelta : null,
      lower_bound: finite(sub?.score?.bootstrap_lower_bound) ? sub.score.bootstrap_lower_bound : null,
      elapsed_seconds: finite(elapsed) ? elapsed : null,
      runtime_efficiency_pp_per_second: finite(scoreDelta) && finite(elapsed) && elapsed > 0 ? (scoreDelta * 100) / elapsed : null,
      eligible: sub?.score?.eligible === true,
      winner: winnerId != null && sub.id === winnerId,
      negative_control: sub?.worker_metrics?.negative_control === true,
      artifact_sha256: sub.artifact_sha256 || null,
      receipt_sha256: sub.receipt_sha256 || null,
    };
  });
}

export function artifactFirewall(submission) {
  return {
    format: 'gradientmine.artifact-firewall.v1',
    protocol_format: 'bounded numeric JSON adapter',
    content_addressed: sha(submission?.artifact_sha256),
    signed_manifest_present: sha(submission?.manifest_sha256),
    receipt_present: sha(submission?.receipt_sha256),
    known_architecture_required: true,
    shape_validation_required: true,
    merged_weight_validation_required: true,
    executable_payload_allowed: false,
    limit: 'These admission controls reduce arbitrary-code and malformed-artifact risk. They do not prove that a model is free of behavioral backdoors, data poisoning, benchmark leakage, or scientific error.',
  };
}

export function modelPassport(job) {
  const winner = job?.winner || null;
  const policy = job?.policy || {};
  const paid = job?.mode === 'devnet' && job?.state === 'SETTLED' && typeof job?.settlement_signature === 'string' && job.settlement_signature.length > 0;
  return {
    format: 'gradientmine.model-passport.v1',
    job_id: job?.id || null,
    task: policy.task || null,
    policy_sha256: job?.policy_sha256 || null,
    parent_sha256: policy.parent_sha256 || null,
    evaluation_commitment: policy.evaluation_sha256 || null,
    model_sha256: winner?.model_sha256 || null,
    artifact_sha256: winner?.artifact_sha256 || null,
    receipt_sha256: winner?.receipt_sha256 || null,
    worker: winner?.worker || null,
    validator: policy.validator || null,
    metric: policy.metric || null,
    baseline_score: finite(job?.baseline_accuracy) ? job.baseline_accuracy : null,
    candidate_score: finite(winner?.candidate_accuracy) ? winner.candidate_accuracy : null,
    observed_delta: finite(winner?.delta) ? winner.delta : null,
    lower_bound: finite(winner?.bootstrap_lower_bound) ? winner.bootstrap_lower_bound : null,
    evaluation_examples: Number.isInteger(winner?.n) ? winner.n : null,
    statistical_rule: policy.statistical_rule || null,
    mode: job?.mode || null,
    paid,
    settlement_signature: paid ? job.settlement_signature : null,
    assurance_level: 'Outcome evaluated by one named evaluator with content-addressed evidence; not proof of training or generalization.',
  };
}
