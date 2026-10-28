import {
  freezePolicy,createSyntheticSubmission,inspectSubmission,evaluateSubmission,
  verifyEvaluationReceipt,beginSettlementRecoveryDrill,reconcileSettlementRecoveryDrill,
  validateSettlementRecoveryDrill,baselineSha256,sha256,canonicalJSON,
} from './local-evaluation.mjs';

const KEY='gradientmine.local-synthetic-run.v1';
const $=id=>document.getElementById(id);
const form=$('bounty-form');
const buttons={freeze:$('freeze-policy'),resume:$('resume-local-run'),interrupt:$('simulate-interruption'),cancel:$('cancel-local-run')};
let checkpoint=null;
let interrupted=false;
let restoreFailed=false;
const fields=['name','model','metric','baseline','target','reward','durationDays','candidates','evaluator'];
const draft=()=>Object.fromEntries(fields.map(k=>[k,$(k).value]).concat([['rights',$('rights').checked]]));
const show=(id,value)=>{$(id).textContent=String(value??'—');};
const setStatus=(message,kind='info')=>{const el=$('local-run-status');el.textContent=message;el.dataset.kind=kind;};
const percent=value=>(value*100).toFixed(2)+'%';
const points=value=>(value>=0?'+':'')+(value*100).toFixed(2)+' pp';

function readyForSimulation(){
  const raw=draft();
  return $('validation-chip').textContent==='DRAFT READY'&&raw.metric==='accuracy'&&Number.isInteger(Number(raw.candidates))&&Number(raw.candidates)>=1&&Number(raw.candidates)<=8;
}

function persist(){
  try { if(checkpoint)localStorage.setItem(KEY,JSON.stringify(checkpoint)); else localStorage.removeItem(KEY); return true; }
  catch {setStatus('Browser storage is unavailable. This local run cannot save a recovery checkpoint.', 'error');return false;}
}

function deleteSavedCheckpoint(){
  try{localStorage.removeItem(KEY);return true;}
  catch{setStatus('Could not delete the saved checkpoint. It may remain in this browser. No deletion is claimed; try again or clear this site’s browser storage.','error');return false;}
}

async function frozenPolicyValid(policy){
  if(!policy||policy.format!=='gradientmine.local-synthetic-policy.v1'||typeof policy.policy_sha256!=='string')return false;
  const {policy_sha256,...body}=policy;
  return await sha256(canonicalJSON(body))===policy_sha256;
}

async function validateCheckpoint(saved){
  const fail=message=>{throw new Error(message);};
  if(!saved||saved.version!==1||!['FROZEN','CANDIDATE_ADMITTED','SYNTHETIC_EVALUATED','INTERRUPTED_CHECKPOINT'].includes(saved.state))fail('Unsupported checkpoint state or version.');
  if(!await frozenPolicyValid(saved.policy))fail('Saved policy checkpoint hash is invalid.');
  const p=saved.policy;
  if(p.status!=='FROZEN_LOCAL_UNFUNDED_SIMULATION'||p.parent?.sha256!==baselineSha256()||p.objective?.metric!=='accuracy'||p.objective?.direction!=='higher'||!Number.isFinite(p.objective?.minimum_delta)||p.objective.minimum_delta<0||p.objective.minimum_delta>1||!Number.isInteger(p.candidate_budget)||p.candidate_budget<1||p.candidate_budget>8||p.local_fixture_candidate_capacity!==1||p.tie_break!=='artifact_sha256_ascending'||p.evaluator?.name!=='Local Synthetic Evaluator'||p.evaluator?.authority!=='single trusted browser module')fail('Frozen policy fields do not match the supported local simulation schema.');
  if(!Array.isArray(saved.submissions)||saved.submissions.length>Math.min(p.candidate_budget,p.local_fixture_candidate_capacity))fail('Candidate checkpoint is malformed or exceeds this fixture’s one-candidate capacity.');
  if(!Array.isArray(saved.submissions)||!saved.policy.source_draft||saved.policy.heldout?.examples!==16||saved.policy.heldout?.secret!==false||saved.policy.settlement?.mode!=='UNFUNDED_LOCAL_ONLY'||saved.policy.settlement?.funds_escrowed!==false||saved.policy.settlement?.transaction_signature!==null)fail('Policy checkpoint is missing required fixture or unfunded fields.');
  const seenIds=new Set(),seenHashes=new Set();
  for(const submission of saved.submissions){
    const inspected=await inspectSubmission(submission,p,[]);
    if(!inspected.admitted||seenIds.has(submission.submission_id)||seenHashes.has(inspected.artifact_sha256))fail('Saved candidate failed signature, shape, lineage, or duplicate checks.');
    seenIds.add(submission.submission_id);seenHashes.add(inspected.artifact_sha256);
  }
  const isInterrupted=saved.state==='INTERRUPTED_CHECKPOINT';
  if(isInterrupted&&!['FROZEN','CANDIDATE_ADMITTED','SYNTHETIC_EVALUATED'].includes(saved.resume_state))fail('Interrupted checkpoint has an invalid resume state.');
  if(!isInterrupted&&Object.hasOwn(saved,'resume_state'))fail('Non-interrupted checkpoint unexpectedly contains a resume state.');
  const effectiveState=isInterrupted?saved.resume_state:saved.state;
  const submissionCount=saved.submissions.length;
  const hasReceipt=Boolean(saved.receipt);
  const hasSettlementProbe=Boolean(saved.settlement_probe);
  const stateConsistent=(
    (effectiveState==='FROZEN'&&submissionCount===0&&!hasReceipt&&!hasSettlementProbe)
    ||(effectiveState==='CANDIDATE_ADMITTED'&&submissionCount===1&&!hasReceipt&&!hasSettlementProbe)
    ||(effectiveState==='SYNTHETIC_EVALUATED'&&submissionCount===1&&hasReceipt)
  );
  if(!stateConsistent)fail('Checkpoint state, admitted candidate, receipt, and settlement probe are inconsistent.');
  if(saved.receipt){
    const verified=await verifyEvaluationReceipt(saved.receipt,p,saved.submissions[0]);
    if(!verified.ok)fail('Saved receipt failed signature/lineage checks: '+verified.reason);
  }
  if(saved.settlement_probe)validateSettlementRecoveryDrill(saved.settlement_probe);
  return true;
}

function showPolicy(){
  const p=checkpoint.policy;
  $('frozen-policy-card').hidden=false;
  $('candidate-admission-card').hidden=false;
  show('frozen-policy-hash',p.policy_sha256);
  show('frozen-parent-hash',p.parent.sha256);
  show('frozen-minimum',`${points(p.objective.minimum_delta)} ${p.objective.metric}`);
  show('frozen-budget',`Planning cap ${p.candidate_budget}; local fixture admits one candidate. Configured tie-break: ${p.tie_break}; not exercised.`);
  show('frozen-evaluator',`${p.evaluator.name} · ${p.evaluator.authority}`);
  show('local-run-state',checkpoint.state);
  buttons.freeze.disabled=true;
  buttons.resume.hidden=true;
  buttons.interrupt.hidden=false;
  buttons.cancel.hidden=false;
  $('load-synthetic-candidate').disabled=Boolean(checkpoint.submissions?.length)||checkpoint.policy.local_fixture_candidate_capacity!==1;
  $('admit-candidate').disabled=Boolean(checkpoint.receipt);
  $('evaluate-candidate').disabled=!checkpoint.submissions?.length||Boolean(checkpoint.receipt);
  $('receipt-card').hidden=!checkpoint.receipt;
}

function checksTable(checks){
  const table=document.createElement('table');table.className='local-check-table';
  const caption=document.createElement('caption');caption.textContent='Candidate admission checks';table.append(caption);
  const head=document.createElement('thead'),tr=document.createElement('tr');
  for(const label of ['Check','Result','Detail']){const th=document.createElement('th');th.scope='col';th.textContent=label;tr.append(th)}
  head.append(tr);table.append(head);
  const body=document.createElement('tbody');
  for(const item of checks){const row=document.createElement('tr');const name=document.createElement('th');name.scope='row';name.textContent=item.name;const status=document.createElement('td');status.textContent=item.ok?'PASS':'REJECTED';status.dataset.state=item.ok?'pass':'fail';const detail=document.createElement('td');detail.textContent=item.detail;row.append(name,status,detail);body.append(row)}
  table.append(body);$('admission-results').replaceChildren(table);
}

async function renderReceipt(){
  if(!checkpoint?.receipt||!checkpoint?.submissions?.[0])return;
  const result=await verifyEvaluationReceipt(checkpoint.receipt,checkpoint.policy,checkpoint.submissions[0]);
  const r=checkpoint.receipt.receipt;
  $('receipt-status').dataset.state=result.ok?'pass':'fail';
  show('receipt-status',result.ok?'SYNTHETIC SIGNATURE MATCH · PUBLIC TEST KEY':'VERIFICATION FAILED');
  show('receipt-summary',`${r.status}. ${result.reason}`);
  show('receipt-hash',checkpoint.receipt.receipt_sha256);
  show('receipt-scores',`${percent(r.baseline_accuracy)} → ${percent(r.candidate_accuracy)}`);
  show('receipt-delta',`${points(r.observed_delta)} / ${points(r.minimum_delta)} minimum · ${r.eligible?'eligible in synthetic fixture':'below frozen rule'}`);
  show('receipt-budget',`${r.candidates_evaluated} evaluated · ${r.candidate_budget} planning cap; no ranking. ${r.tie_break} configured, not exercised.`);
  show('receipt-lineage',`${r.parent_sha256} → ${r.candidate_model_sha256} · adapter ${r.candidate_artifact_sha256}`);
  show('receipt-stats',`${r.evaluation_examples} examples. ${r.statistical_limit}`);
  show('receipt-evaluator',r.evaluator_trust_boundary);
  show('receipt-settlement',`${r.settlement_status}; funds escrowed: no; no transaction signature exists; payouts: ${r.payout_count}.`);
  const probe=checkpoint.settlement_probe;
  if(probe){
    $('recover-ambiguous-settlement').disabled=probe.status==='RECONCILED_NO_TRANSACTION';
    show('settlement-recovery-status',`${probe.status}: no transaction was sent, no signature exists, and payout count remains ${probe.payout_count}. Recovery checks: ${probe.recovery_checks}. Repeating reconciliation is idempotent.`);
  }
}

function render(){
  if(interrupted){
    $('frozen-policy-card').hidden=true;$('candidate-admission-card').hidden=true;$('receipt-card').hidden=true;
    buttons.resume.hidden=false;buttons.freeze.disabled=true;buttons.interrupt.hidden=true;buttons.cancel.hidden=false;
    return;
  }
  if(checkpoint){
    showPolicy();
    if(checkpoint.submissions?.[0]){
      const s=checkpoint.submissions[0];
      if(!$('candidate-json').value)$('candidate-json').value=JSON.stringify(s,null,2);
      show('admitted-lineage',`Admitted synthetic candidate ${s.submission_id} · artifact ${s.artifact_sha256} · baseline ${s.artifact.baseline_sha256}.`);
      $('admitted-lineage').hidden=false;
    }
    if(checkpoint.receipt)renderReceipt();
  }else{
    $('frozen-policy-card').hidden=true;$('candidate-admission-card').hidden=true;$('receipt-card').hidden=true;
    buttons.resume.hidden=true;buttons.interrupt.hidden=true;buttons.cancel.hidden=true;
  buttons.freeze.disabled=restoreFailed||!readyForSimulation();
  }
  $('clear-local-checkpoint').hidden=!restoreFailed;
}

form.addEventListener('input',()=>{
  if(!checkpoint&&!interrupted){buttons.freeze.disabled=restoreFailed||!readyForSimulation();}
});
form.addEventListener('change',()=>{
  if(!checkpoint&&!interrupted){buttons.freeze.disabled=restoreFailed||!readyForSimulation();
    if($('metric').value!=='accuracy')setStatus('Research Lab supports separate retrieval, refusal, quality and efficiency task families. The Digits escrow path here is accuracy-only.','info');
    else if(Number(draft().candidates)>8)setStatus('This draft can still be exported, but the Digits escrow path and synthetic evaluation cap the candidate budget at 8.','info');
    else if(readyForSimulation())setStatus('Draft is valid. Freeze it to begin a synthetic, unfunded browser-only run.','info');
  }
});

buttons.freeze.addEventListener('click',async()=>{
  buttons.freeze.disabled=true;
  try{
    const policy=await freezePolicy(draft());
    checkpoint={version:1,state:'FROZEN',policy,submissions:[],receipt:null,settlement_probe:null,cancelled:false};
    if(!persist()){checkpoint=null;buttons.freeze.disabled=restoreFailed||!readyForSimulation();return;}
    setStatus('Policy frozen locally. Its hash binds the draft, baseline, evaluator, minimum delta, candidate budget, tie-break and disclosed synthetic fixture.','ok');render();
  }catch(error){setStatus(error.message,'error');buttons.freeze.disabled=!readyForSimulation();}
});

$('load-synthetic-candidate').addEventListener('click',async()=>{
  try{
    const submission=await createSyntheticSubmission(checkpoint.policy);
    $('candidate-json').value=JSON.stringify(submission,null,2);
    $('admission-results').textContent='Synthetic candidate loaded and signed locally. No wallet was used.';
    $('admit-candidate').disabled=false;
  }catch(error){setStatus(`Could not create the local synthetic signature: ${error.message}`,'error');}
});

$('admit-candidate').addEventListener('click',async()=>{
  try{
    const submission=JSON.parse($('candidate-json').value);
    const existing=checkpoint.submissions||[];
    const result=await inspectSubmission(submission,checkpoint.policy,existing);
    checksTable(result.checks);
    if(!result.admitted){setStatus('Candidate rejected. Failed checks stay visible; no evaluation was run.','error');return;}
    if(existing.length>=Math.min(checkpoint.policy.candidate_budget,checkpoint.policy.local_fixture_candidate_capacity)){
      setStatus('Candidate rejected: this synthetic fixture supports one candidate per run. No candidate ranking occurs and the configured hash tie-break is not exercised.','error');return;
    }
    const previous=checkpoint;
    checkpoint={...checkpoint,submissions:[...existing,{...submission,artifact_sha256:result.artifact_sha256}]};
    checkpoint.state='CANDIDATE_ADMITTED';
    if(!persist()){checkpoint=previous;render();setStatus('Candidate was not saved to the local checkpoint, so it was not admitted for evaluation.','error');return;}
    setStatus('Candidate admitted to this synthetic local run. Signature verification authenticates the generated fixture only.','ok');render();
  }catch(error){setStatus(`Candidate rejected: ${error.message}`,'error');}
});

$('evaluate-candidate').addEventListener('click',async()=>{
  $('evaluate-candidate').disabled=true;
  try{
    const envelope=await evaluateSubmission(checkpoint.submissions[0],checkpoint.policy,checkpoint.submissions.slice(1));
    const previous=checkpoint;
    checkpoint={...checkpoint,receipt:envelope,state:'SYNTHETIC_EVALUATED'};
    if(!persist()){checkpoint=previous;setStatus('Receipt could not be saved to this browser. The checkpoint remains at candidate admission.','error');render();return;}
    setStatus('Synthetic evaluation finished. This is a fixture result, not the recorded Digits training run.','ok');
    $('receipt-card').hidden=false;await renderReceipt();
  }catch(error){setStatus(`Evaluation stopped: ${error.message}`,'error');$('evaluate-candidate').disabled=false;}
});

buttons.interrupt.addEventListener('click',()=>{
  if(!checkpoint)return;
  const previous=checkpoint.state;
  checkpoint.resume_state=checkpoint.state;
  checkpoint.state='INTERRUPTED_CHECKPOINT';
  if(!persist()){checkpoint.state=previous;delete checkpoint.resume_state;setStatus('Could not save the checkpoint. The run remains in this page and was not marked paused.','error');render();return;}
  interrupted=true;
  setStatus('Simulation paused. The local checkpoint is saved; resume to continue from the frozen policy and exact admitted candidate.','ok');render();
});

buttons.resume.addEventListener('click',async()=>{
  try{
    if(!checkpoint)throw new Error('No saved checkpoint is available.');
    await validateCheckpoint(checkpoint);
    const previous=checkpoint;
    checkpoint={...checkpoint,state:checkpoint.resume_state||(checkpoint.receipt?'SYNTHETIC_EVALUATED':checkpoint.submissions?.length?'CANDIDATE_ADMITTED':'FROZEN')};
    delete checkpoint.resume_state;
    if(!persist()){checkpoint=previous;setStatus('Checkpoint passed integrity checks but could not be updated in browser storage. It remains paused.','error');render();return;}
    interrupted=false;
    setStatus('Checkpoint resumed. Frozen policy and any admitted artifact were revalidated before continuing.','ok');render();
  }catch(error){setStatus(`Checkpoint rejected: ${error.message}`,'error');}
});

buttons.cancel.addEventListener('click',()=>{
  if(!deleteSavedCheckpoint())return;
  checkpoint=null;interrupted=false;restoreFailed=false;
  $('candidate-json').value='';$('admission-results').textContent='Candidate has not been checked.';$('admitted-lineage').hidden=true;
  setStatus('Local simulation cancelled. The frozen policy, candidate and synthetic receipt checkpoint were deleted from this browser. No transaction existed.','info');
  render();
});

$('clear-local-checkpoint').addEventListener('click',()=>{
  if(!deleteSavedCheckpoint())return;
  restoreFailed=false;checkpoint=null;interrupted=false;
  setStatus('Unreadable checkpoint deleted from this browser. No run was resumed.','info');render();
});

$('simulate-ambiguous-settlement').addEventListener('click',()=>{
  const previous=checkpoint;checkpoint=beginSettlementRecoveryDrill(checkpoint);
  if(!persist()){checkpoint=previous;setStatus('Settlement drill could not be saved; no recovery state was changed.','error');return;}
  renderReceipt();
});
$('recover-ambiguous-settlement').addEventListener('click',()=>{
  try{const previous=checkpoint;checkpoint=reconcileSettlementRecoveryDrill(checkpoint);if(!persist()){checkpoint=previous;setStatus('Recovery result could not be saved; the saved no-transaction state is unchanged.','error');return;}renderReceipt();}
  catch(error){show('settlement-recovery-status',error.message);}
});
$('download-local-receipt').addEventListener('click',()=>{
  if(!checkpoint?.receipt)return;
  const file=new Blob([JSON.stringify({policy:checkpoint.policy,submission:checkpoint.submissions[0],...checkpoint.receipt},null,2)+'\n'],{type:'application/json'});
  const url=URL.createObjectURL(file),a=document.createElement('a');a.href=url;a.download='gradientmine-synthetic-local-receipt.json';document.body.append(a);a.click();a.remove();URL.revokeObjectURL(url);
});

try{
  const saved=localStorage.getItem(KEY);
  if(saved){
    const parsed=JSON.parse(saved);
    if(parsed?.version===1&&parsed?.policy?.format==='gradientmine.local-synthetic-policy.v1'){
      checkpoint=parsed;interrupted=true;
      setStatus('A local checkpoint was found. Resume to recheck its policy and candidate before continuing.','info');
    }else {restoreFailed=true;throw new Error('Unexpected checkpoint format.');}
  }
}catch(error){restoreFailed=true;setStatus(`Saved checkpoint is unreadable and was not resumed: ${error.message}`,'error');}
render();
