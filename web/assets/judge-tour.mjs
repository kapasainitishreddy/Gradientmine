import {auditLocalEvidence} from './proof-audit.mjs';
/**
 * An evidence-first judge walkthrough. Performance figures are fetched from
 * the same recorded-run JSON used by the read-only public application.
 * This page does not itself validate Ed25519 signatures: the homepage inspector does.
 */
const root=document.getElementById('tour-stage');
const steps=[...document.querySelectorAll('[data-step]')];
const panels=[...document.querySelectorAll('[data-panel]')];
const $=id=>document.getElementById(id);
let current=0;
let loadedEvidence=null;

const text=(id,value)=>{ $(id).textContent=String(value); };
const pct=v=>Number.isFinite(v) ? (v*100).toFixed(2)+'%' : '—';
const points=v=>Number.isFinite(v) ? (v>=0?'+':'')+(v*100).toFixed(2)+' pp' : '—';
const abbreviated=v=>typeof v==='string'&&v.length>16 ? v.slice(0,9)+'…'+v.slice(-7) : String(v??'—');

function show(index,focus=false) {
  current=Math.max(0,Math.min(panels.length-1,index));
  panels.forEach((p,i)=>{p.hidden=i!==current});
  steps.forEach((button,i)=>{
    if(i===current) button.setAttribute('aria-current','step');
    else button.removeAttribute('aria-current');
  });
  $('tour-number').textContent=String(current+1).padStart(2,'0')+' / 06';
  $('tour-progress').textContent='STEP '+(current+1)+' OF '+panels.length;
  $('tour-progress-bar').style.width=((current+1)/panels.length*100)+'%';
  $('tour-back').disabled=current===0;
  $('tour-next').disabled=current===panels.length-1;
  $('tour-next').textContent=current===panels.length-1?'Walkthrough complete':'Next →';
  if(focus)root.focus({preventScroll:true});
}
steps.forEach(b=>b.addEventListener('click',()=>show(Number(b.dataset.step),true)));
$('tour-back').addEventListener('click',()=>show(current-1,true));
$('tour-next').addEventListener('click',()=>show(current+1,true));
document.addEventListener('keydown',event=>{
  if(event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;
  if(['INPUT','TEXTAREA','SELECT'].includes(document.activeElement?.tagName))return;
  if(event.key==='ArrowRight'){event.preventDefault();show(current+1,true)}
  if(event.key==='ArrowLeft'){event.preventDefault();show(current-1,true)}
});
show(0);

function ensureRun(data) {
  const job=data?.job;
  const w=job?.winner;
  if(data?.mode!=='local'||job?.mode!=='local'||job?.state!=='EVALUATED'
    ||job?.settlement_signature||job?.funding_signature
    ||!Number.isFinite(job?.baseline_accuracy)
    ||!Number.isFinite(w?.candidate_accuracy)
    ||!Number.isFinite(w?.delta)
    ||!Number.isFinite(w?.bootstrap_lower_bound)
    ||!Number.isInteger(w?.n)||w.n<=0
    ||!Array.isArray(job?.submissions)||!job.submissions.length
    ||!job?.policy||!w.eligible)throw new Error('The expected local evidence is missing or malformed.');
  return job;
}

function populate(job) {
  const p=job.policy,w=job.winner;
  text('tour-metric',p.metric||'Not recorded');
  text('tour-minimum',points(p.minimum_delta));
  text('tour-budget',Number.isInteger(p.max_candidates)?p.max_candidates:'—');
  text('tour-policy-hash',abbreviated(job.policy_sha256));
  text('tour-worker-count',job.submissions.length+' recorded processes');
  text('tour-baseline',pct(job.baseline_accuracy));
  text('tour-selected',pct(w.candidate_accuracy));
  text('tour-delta',points(w.delta));
  text('tour-lower-bound',points(w.bootstrap_lower_bound));
  text('tour-examples',w.n+' held-out examples • approximate adjusted lower bound • signed receipt inspectable in the main product');
  const list=$('tour-workers');
  list.replaceChildren();
  for(const [i,s] of job.submissions.entries()) {
    const row=document.createElement('div');
    row.className='evidence-worker';
    const title=document.createElement('span');
    title.textContent='Worker '+(i+1)+(s.worker_metrics?.negative_control?' · disclosed negative control':'');
    const score=document.createElement('strong');
    score.textContent=pct(s.score?.candidate_accuracy);
    const state=document.createElement('small');
    state.textContent=s.id===w.submission_id?'SELECTED WINNER':s.score?.eligible?'ELIGIBLE, NOT SELECTED':'BELOW THE FROZEN RULE';
    row.append(title,score,state);
    list.append(row);
  }
  $('evidence-status').textContent='Loaded actual recorded local job '+abbreviated(job.id)+'. Performance is reported from public JSON; verify hash/signatures in the product inspector.';
  $('evidence-status').classList.add('loaded');
}
fetch('./assets/recorded-run.json',{cache:'no-store'})
  .then(async r=>{
    if(!r.ok)throw new Error('HTTP '+r.status);
    return r.json();
  })
  .then(data=>{const job=ensureRun(data);loadedEvidence=data;populate(job);$('run-evidence-audit').disabled=false;})
  .catch(()=>{
    $('evidence-status').textContent='Recorded evidence could not be loaded. No numbers are claimed on this page; inspect the signed evidence from the homepage or repository.';
    $('tour-evidence-source').textContent='SOURCE UNAVAILABLE — NO VERIFIED RESULT SHOWN HERE';
  });


/* Read-only public browser audit: no custom validator API, no wallet, no SOL. */
$('run-evidence-audit').addEventListener('click',async()=>{
  if(!loadedEvidence)return;
  const button=$('run-evidence-audit'),display=$('evidence-audit-result');
  button.disabled=true;
  display.dataset.result='running';
  display.textContent='Checking actual downloaded public evidence bytes…';
  try {
    const result=await auditLocalEvidence(loadedEvidence,async hash=>{
      const response=await fetch('./assets/artifacts/'+hash+'.json',{
        cache:'no-store',signal:AbortSignal.timeout(15000),
      });
      if(!response.ok)throw Error('Artifact fetch failed with HTTP '+response.status+'.');
      return new Uint8Array(await response.arrayBuffer());
    },progress=>{
      display.textContent='Verified '+progress.completed+'/'+progress.total+' artifact hashes…';
    });
    display.dataset.result='pass';
    display.textContent='CHECKED: '+result.artifactsVerified+' artifact hashes, '+
      result.signaturesVerified+' Ed25519 signatures, policy and winner references. '+
      'This does not prove training, model accuracy or a live Devnet payout.';
  }catch(error){
    display.dataset.result='fail';
    display.textContent='AUDIT INCOMPLETE / FAILED: '+error.message+
      ' No verification pass is claimed.';
  }finally{
    button.disabled=false;
  }
});
