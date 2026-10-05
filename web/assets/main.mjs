import {WalletSession} from './wallet.mjs';
import {bytes,base64,sha256,verifyEnvelope,short,percent,delta,lamports,node,explorer,solToLamports,equal} from './core.mjs';
import {validateIntent,validateWalletSignature} from './wire.mjs';

const $=id=>document.getElementById(id),state={config:null,recorded:null,jobs:[],job:null,selected:null,busy:false,evidence:null};
const assetRoot=new URL('./',import.meta.url);
let wallet=null,creationKey=null,pendingAction=null;
wallet=new WalletSession(()=>queueMicrotask(()=>{renderWallet();if(state.job)renderDetail();}));
const label=s=>({AWAITING_FUNDING:'Awaiting escrow',OPEN:'Accepting workers',EVALUATED:'Evaluated · not paid',NO_WINNER:'No eligible winner',SETTLING:'Payout pending',SETTLED:'Payout finalized',REFUNDED:'Refund finalized',ELIGIBLE:'Eligible',REJECTED:'Below threshold',REGISTERED:'Registered',AWAITING_REGISTRATION:'Registration pending'}[s]||s);
const dt=t=>Number.isFinite(t)?new Date(t*1000).toLocaleString():'Not recorded';
function notice(text,error=true){$('notice').textContent=text;$('notice').hidden=!text;$('notice').classList.toggle('success',!error);}
async function api(path,body,extra={}){
 const response=await fetch(path,{method:body===undefined?'GET':'POST',headers:{...(body===undefined?{}:{'Content-Type':'application/json'}),...(wallet?.token?{Authorization:`Bearer ${wallet.token}`} : {}),...extra},...(body===undefined?{}:{body:JSON.stringify(body)}),signal:AbortSignal.timeout(90000),cache:'no-store'});
 let value;try{value=await response.json();}catch{throw Error('The API did not return JSON. Confirm this is a running GradientMine server.');}
 if(!response.ok){if(response.status===401){wallet?.clear();renderWallet();}throw Error(typeof value.error==='string'?value.error:`Request failed (${response.status}). Retry after checking the server.`);}
 return value;
}
function button(text,fn,cls='button secondary'){const b=node('button',text,cls);b.type='button';b.addEventListener('click',()=>Promise.resolve().then(fn).catch(e=>notice(e.message)));return b;}
function append(parent,...children){for(const c of children)if(c)parent.append(c);return parent;}
function textLink(text,url){const a=node('a',text);a.href=url;a.target='_blank';a.rel='noopener noreferrer';return a;}
function code(text){return node('code',text,'hash');}
function modeText(){
 if(state.recorded)return `Recorded local experiment · ${dt(state.recorded.recorded_at)} · Read-only evidence, not a live network. No blockchain payment.`;
 return state.config.mode==='devnet'?'Solana Devnet · Test funds only · One named evaluator · Connection is checked before each transaction.':'Live local server · Real training and evaluation · No blockchain or token payments.';
}
async function start(){
 try{
  state.config=await api('/api/config');
  if(!['local','devnet'].includes(state.config.mode)||state.config.origin!==location.origin)throw Error('Server authentication origin differs from this website. Configure GM_ORIGIN to this exact origin.');
  await refresh();
 }catch(e){
  try{
   const r=await fetch(new URL('recorded-run.json',assetRoot));if(!r.ok)throw Error('No recorded evidence');
   const run=await r.json();if(run.format!=='gradientmine.recorded-run.v1'||run.mode!=='local'||run.job.mode!=='local'||run.job.settlement_signature)throw Error('Unexpected recorded-run format');
   state.recorded=run;state.config={mode:'local',validator:run.job.policy.validator};state.jobs=[run.job];state.job=run.job;state.selected=run.job.id;
   renderJobs();renderDetail();
  }catch{notice(e.message);$('detail').replaceChildren(append(node('div',null,'empty'),node('h2','The server is not reachable'),node('p','Start the API using the README, then reload this page. No activity has been invented.'),button('Retry connection',()=>location.reload())));}
 }
 $('mode-banner').textContent=state.config?modeText():'Not connected · No verified activity available';
 renderWallet();renderCommands();
}
async function refresh(){
 if(state.recorded){renderJobs();renderDetail();return;}
 const result=await api('/api/jobs');state.jobs=result.jobs;
 state.selected=state.selected||state.jobs[0]?.id||null;
 if(state.selected)state.job=await api(`/api/jobs/${encodeURIComponent(state.selected)}`);
 else state.job=null;
 renderJobs();renderDetail();renderCommands();
}
function renderJobs(){
 const filter=$('job-filter').value;
 const jobs=state.jobs.filter(j=>filter==='all'||(filter==='open'?j.state==='OPEN':['EVALUATED','SETTLED','NO_WINNER'].includes(j.state)));
 const items=jobs.map(j=>{
  const b=button('',async()=>{state.selected=j.id;state.job=state.recorded?j:await api(`/api/jobs/${encodeURIComponent(j.id)}`);renderJobs();renderDetail();renderCommands();},'job');
  b.classList.toggle('selected',state.selected===j.id);b.setAttribute('aria-pressed',String(state.selected===j.id));b.setAttribute('aria-current',String(state.selected===j.id));
  append(b,node('span',label(j.state),'state'),node('strong',j.title),node('small',j.mode==='devnet'?`${lamports(j.policy.reward_lamports)} · Devnet`:'Local · no payment'),node('small',short(j.id)));
  return b;
 });
 $('jobs').replaceChildren(...(items.length?items:[append(node('div',null,'empty'),node('p','No matching bounties.'),node('small',state.recorded?'Change the filter to inspect the recorded run.':'Create the first experiment to get started.'))]));
}
function metric(title,value,detail){return append(node('div',null,'metric'),node('label',title),node('strong',value),node('small',detail));}
function evidenceButton(title,hash,signer=null){const b=button(title,()=>inspect(hash,signer),'text-button');b.disabled=!hash;return b;}
function renderDetail(){
 const root=$('detail'),j=state.job;if(!j){root.replaceChildren(append(node('div',null,'empty'),node('h2','A result starts with a bounty'),node('p','Connect your wallet and define the improvement you want to measure.'),button('Create an experiment',()=>openCreate())));return;}
 const w=j.winner,p=j.policy,subs=j.submissions||[],finished=['EVALUATED','SETTLING','SETTLED','NO_WINNER'].includes(j.state),paid=j.state==='SETTLED'&&j.settlement_signature;
 const head=append(node('div',null,'detail-header'),append(node('div'),node('span',label(j.state),'state'),node('h2',j.title)),node('span',j.mode==='devnet'?`${lamports(p.reward_lamports)} reward`:'No monetary reward','reward'));
 const meta=append(node('div',null,'detail-meta'),node('span','digits-lora-v1 · Neural classifier'),node('span',`Cutoff: ${dt(p.deadline)}`),node('span',`Minimum: ${delta(p.minimum_delta)}`));
 const pipeline=node('div',null,'pipeline');
 [['Bounty',true],['Escrow',j.mode==='devnet'&&!!j.funding_signature],['Train',subs.length>0],['Evaluate',finished],['Payout',!!paid]].forEach(([text,done])=>append(pipeline,append(node('div',null,`stage${done?' done':''}`),node('span',done?'✓':'·','dot'),node('span',text==='Escrow'&&j.mode==='local'?'No escrow':text==='Payout'&&j.mode==='local'?'No payout':text))));
 const metrics=append(node('div',null,'metric-band'),metric('Frozen parent',finished?percent(j.baseline_accuracy):'—','Held-out accuracy'),metric('Best eligible model',w?percent(w.candidate_accuracy):'—',w?'Eligible is not the same as paid':'No eligible result yet'),metric('Measured improvement',w?delta(w.delta):'—',w?`${w.n} held-out examples`:'Scores withheld until cutoff'));
 const table=node('table');const caption=node('caption','Submitted experiments');caption.className='sr-only';
 const thead=node('thead'),hr=node('tr');for(const t of ['Worker','Held-out result','Decision','Evidence']){const th=node('th',t);th.scope='col';hr.append(th);}thead.append(hr);const tbody=node('tbody');
 for(const s of subs){
  const tr=node('tr',null,w?.submission_id===s.id?'winner':null);const who=node('td');append(who,code(short(s.worker)),node('small',s.worker_metrics?.negative_control?'Disclosed negative control':`Worker-reported ${s.worker_metrics?.device||'device unknown'}`));
  const result=node('td');append(result,node('strong',s.score?percent(s.score.candidate_accuracy):'Awaiting evaluation'),node('small',s.score?delta(s.score.delta):'No held-out score disclosed'));
  const decision=node('td');append(decision,node('span',w?.submission_id===s.id?'Selected winner':label(s.state),'state'));
  const evidence=node('td');append(evidence,evidenceButton('Adapter',s.artifact_sha256),evidenceButton('Manifest',s.manifest_sha256,s.worker),s.receipt_sha256?evidenceButton('Receipt',s.receipt_sha256,p.validator):null);
  append(tr,who,result,decision,evidence);tbody.append(tr);
 }
 if(!subs.length){const tr=node('tr'),td=node('td','No submissions yet. Start a worker using the commands below.');td.colSpan=4;tr.append(td);tbody.append(tr);}
 append(table,caption,thead,tbody);const tableWrap=append(node('div',null,'table-wrap'),table);
 const proof=node('div',null,'proof-note');
 if(w)append(proof,node('strong',`Lower confidence bound: ${delta(w.bootstrap_lower_bound)}`),node('p','Paired bootstrap, one-sided with a predeclared eight-candidate correction. Approximate, IID-dependent evidence. This does not establish resistance to public benchmark leakage.'));
 else append(proof,node('p',finished?'No candidate met the declared improvement and confidence rules. A Devnet refund becomes available after the on-chain timeout.':'The server withholds held-out scores until submission closes. Public validation metrics claimed by workers are not reward eligibility evidence.'));
 const lineage=append(node('section',null,'lineage'),node('h3','Model lineage'));
 const lineagePath=node('div',null,'lineage-path');append(lineagePath,append(node('div',null,'lineage-node'),node('small',p.parent_job_id?'Previous winning model':'Budget-limited parent'),code(short(p.parent_sha256)),evidenceButton('Inspect parent',p.parent_sha256)));
 if(w)append(lineagePath,node('span','→','lineage-arrow'),append(node('div',null,'lineage-node selected'),node('small','Accepted candidate'),code(short(w.model_sha256)),evidenceButton('Inspect model',w.model_sha256)));
 lineage.append(lineagePath);lineage.append(node('p',`${j.lineage?.length||0} prior accepted round(s). Parent relationships are recorded; this release does not distribute lineage royalties.`,'fine'));
 const actions=node('div',null,'actions');
 if(!state.recorded){
  if(j.mode==='devnet'&&j.creator===wallet?.account?.address&&j.state==='AWAITING_FUNDING')actions.append(button('Fund Devnet escrow',()=>prepareTransaction('fund')));
  if(j.state==='OPEN'&&Date.now()/1000>=p.deadline)actions.append(button('Evaluate candidates',()=>mutateJob('evaluate')));
  if(j.mode==='devnet'&&['EVALUATED','SETTLING'].includes(j.state)&&w)actions.append(button('Confirm winner payout',()=>mutateJob('settle')));
  if(j.mode==='devnet'&&j.creator===wallet?.account?.address&&!['SETTLED','REFUNDED'].includes(j.state)&&Date.now()/1000>=p.refund_after)actions.append(button('Claim timeout refund',()=>prepareTransaction('refund')));
  if(j.settlement_warning&&j.state==='SETTLING')actions.append(button('Recover expired settlement',()=>mutateJob('recover-settlement')));
  if(w && (j.mode==='local'&&j.state==='EVALUATED'||j.state==='SETTLED'))actions.append(button('Improve this winning model',()=>openCreate(j)));
  const pending=readPending(j.id);if(pending)actions.append(button('Recheck pending transaction',()=>confirmPending(pending)));
 }
 const audit=append(node('section',null,'audit'),node('h3','Evidence trail'));
 const dl=node('dl');
 for(const [name,value] of [['Mode',j.mode==='devnet'?'Solana Devnet':'Local, no on-chain payments'],['Named validator',p.validator],['Policy commitment',p.train_sha256?j.policy_sha256:'Unavailable'],['Held-out commitment',p.evaluation_sha256],['Submission cutoff',dt(p.deadline)],['Timeout refund',j.mode==='devnet'?dt(p.refund_after):'Not applicable'],['Creator',j.creator]]){append(dl,node('dt',name),append(node('dd'),code(value)));}
 append(audit,dl,evidenceButton('Inspect immutable policy',j.policy_sha256));
 for(const [name,signature,kind] of [['Funding',j.funding_signature,'tx'],['Payout',j.settlement_signature,'tx'],['Refund',j.refund_signature,'tx'],['Bounty account',j.bounty_address,'address']]){const url=explorer(j.mode,signature,kind);if(url)append(audit,node('p'),textLink(`${name} on Solana Explorer`,url));}
 if(!paid)audit.append(node('p','No finalized payout is claimed for this bounty.','fine'));
 if(j.settlement_warning)audit.append(node('p',`Settlement requires attention: ${j.settlement_warning}`,'form-error'));
 const events=append(node('details',null,'events'),node('summary','Protocol event log'));
 for(const e of j.events||[])events.append(append(node('p'),node('small',dt(e.created)),node('strong',` ${e.kind}`),node('span',` · ${e.message}`)));
 root.replaceChildren(head,meta,pipeline,metrics,tableWrap,proof,lineage,actions,audit,events);
}
function renderWallet(){
 if(!wallet)return;
 $('wallet-button').textContent=wallet.account?`${short(wallet.account.address)} · Disconnect`:'Connect wallet';
 $('wallet-button').disabled=!!state.recorded||!state.config;
 $('create-button').disabled=!!state.recorded||!state.config;
 const list=$('wallet-list');list.replaceChildren();
 for(const w of wallet.wallets)list.append(button(w.name||'Solana wallet',async()=>{await wallet.connect(w,api);$('wallet-dialog').close();notice('Wallet authenticated. No funds have moved.',false);renderWallet();}));
 if(!wallet.wallets.size)list.append(node('p','No compatible wallet detected. Open this page in a browser with Phantom or another Solana Wallet Standard wallet enabled. Then retry.'));
}
function openCreate(parent=null){
 if(state.recorded)throw Error('This is a read-only recorded run. Start the API to create a bounty.');
 if(!wallet.account){$('wallet-dialog').showModal();return;}
 const f=$('create-form');f.elements.parent.value=parent?.id||'';
 f.elements.reward.disabled=state.config.mode==='local';f.elements.reward.value=state.config.mode==='local'?'0':'0.025';
 $('reward-help').textContent=state.config.mode==='local'?'Local mode has no funds or token payouts. Reward is fixed at zero.':'0.001–1 Devnet SOL. Account rent and transaction fees are shown before wallet approval. Test funds only.';
 $('parent-help').textContent=parent?`Uses the accepted model from “${parent.title}”.`:'Starts from the reproducible, budget-limited digits baseline. Not an LLM or a state-of-the-art baseline.';
 $('create-error').textContent='';creationKey=null;$('create-dialog').showModal();
}
async function createBounty(e){
 e.preventDefault();if(state.busy)return;const f=e.target,submit=f.querySelector('[type=submit]');state.busy=true;submit.disabled=true;$('create-error').textContent='';
 try{
  const values={title:f.elements.title.value.trim(),duration_seconds:Number(f.elements.duration.value),reward_lamports:solToLamports(f.elements.reward.value),minimum_delta:Number(f.elements.minimum.value)/100,parent_job_id:f.elements.parent.value||null};
  const encoded=JSON.stringify(values);if(!creationKey||creationKey.body!==encoded)creationKey={body:encoded,key:crypto.randomUUID()};
  const j=await api('/api/jobs',values,{'Idempotency-Key':creationKey.key});state.selected=j.id;$('create-dialog').close();await refresh();notice(j.mode==='devnet'?'Bounty draft created. Use “Fund Devnet escrow” to approve funding in your wallet.':'Local bounty created. Start a worker to submit an actual experiment.',false);
 }catch(err){$('create-error').textContent=err.message;}finally{state.busy=false;submit.disabled=false;}
}
async function mutateJob(action){if(!wallet.account){$('wallet-dialog').showModal();return;}notice('Checking protocol state…',false);await api(`/api/jobs/${state.job.id}/${action}`,{});await refresh();notice('Protocol state refreshed from server evidence.',false);}
async function prepareTransaction(action){
 if(!wallet.account)throw Error('Connect the creator wallet first.');
 const j=await api(`/api/jobs/${state.job.id}`),intent=await api(`/api/jobs/${j.id}/transaction`,{action});
 await validateIntent(intent,action,j,state.config,wallet.account.address);
 pendingAction={action,intent,job:j};$('transaction-summary').textContent=action==='fund'?`Escrow ${lamports(j.policy.reward_lamports)} as a test reward.`:'Refund the remaining test reward to the bounty creator.';
 $('transaction-details').textContent=JSON.stringify({action,network:'Solana Devnet',program:intent.program_id,payer:intent.payer,accounts:intent.accounts,reward_lamports:intent.reward_lamports,network_fee_lamports:intent.fee_lamports,account_rent_lamports:intent.rent_lamports,cutoff:dt(j.policy.deadline),refund_after:dt(j.policy.refund_after)},null,2);
 $('transaction-dialog').showModal();
}
function pendingKey(id){return `gradientmine.pending.${location.origin}.${id}`;}
function readPending(id){try{const p=JSON.parse(localStorage.getItem(pendingKey(id)));return p&&p.job_id===id&&['fund','refund'].includes(p.action)&&explorer('devnet',p.signature)?p:null;}catch{return null;}}
async function approveTransaction(){
 const b=$('approve-transaction');b.disabled=true;
 try{
  const p=pendingAction;if(!p)throw Error('No reviewed transaction.');
  const raw=await wallet.sign(p.intent);const signature=await validateWalletSignature(bytes(p.intent.transaction_base64),raw,wallet.account.address);
  const pending={job_id:p.job.id,action:p.action,signature};localStorage.setItem(pendingKey(p.job.id),JSON.stringify(pending));
  await api(`/api/jobs/${p.job.id}/broadcast`,{action:p.action,transaction_base64:base64(raw)});
  $('transaction-dialog').close();await confirmPending(pending);
 }finally{b.disabled=false;}
}
async function confirmPending(p){
 if(!wallet.account)throw Error('Reconnect the same wallet to confirm this transaction.');
 notice('Waiting for finalized chain evidence. A broadcast alone is not a payment.',false);
 try{await api(`/api/jobs/${p.job_id}/confirm`,{action:p.action,signature:p.signature});localStorage.removeItem(pendingKey(p.job_id));await refresh();notice('Finalized transaction confirmed against the exact bounty action.',false);}
 catch(e){await refresh();throw Error(`${e.message} The transaction remains pending in this browser. Use “Recheck pending transaction”; do not assume success.`);}
}
async function inspect(hash,signer=null){
 if(!/^[a-f0-9]{64}$/.test(hash||''))throw Error('Invalid artifact reference.');
 $('evidence-dialog').showModal();$('evidence-title').textContent=signer?'Signed evidence':'Artifact evidence';$('evidence-hash').textContent=hash;$('evidence-json').textContent='';$('evidence-status').textContent='Checking exact bytes…';$('download-evidence').disabled=true;state.evidence=null;
 try{
  const url=state.recorded?new URL(`artifacts/${hash}.json`,assetRoot):`/api/artifacts/${hash}`;
  const r=await fetch(url,{cache:'no-store',signal:AbortSignal.timeout(15000)});if(!r.ok)throw Error('Artifact unavailable. A hash alone does not guarantee storage availability.');
  const raw=new Uint8Array(await r.arrayBuffer());if(raw.length>262144)throw Error('Artifact exceeds the supported limit.');
  if(await sha256(raw)!==hash)throw Error('Artifact SHA-256 mismatch. Do not trust this content.');
  const value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));
  if(signer&&!await verifyEnvelope(value,signer))throw Error('Signer or Ed25519 signature verification failed.');
  if(hash===state.job?.policy_sha256&&!equal(value,state.job.policy))throw Error('Policy bytes differ from the displayed bounty.');
  state.evidence={hash,raw};$('evidence-status').textContent=signer?'SHA-256 matches · Ed25519 signature verified against the expected signer.':'SHA-256 matches the referenced exact bytes.';
  $('evidence-json').textContent=JSON.stringify(value,null,2);$('download-evidence').disabled=false;
 }catch(e){$('evidence-status').textContent=e.message;}
}
function renderCommands(){
 const j=state.job,apiUrl=state.recorded?'http://127.0.0.1:8000':location.origin;
 const commands=['git clone https://github.com/kapasainitishreddy/Gradientmine','cd Gradientmine','python -m venv .venv','# Activate .venv (see README for Windows / macOS / Linux)','python -m pip install -e ".[chain]"','gradientmine identity --out worker-identity.json',`gradientmine worker --api ${JSON.stringify(apiUrl)} \\\n  --job ${state.recorded?'YOUR_LIVE_BOUNTY_ID':j?.id||'YOUR_LIVE_BOUNTY_ID'} \\\n  --identity worker-identity.json${state.config?.mode==='devnet'?` \\\n  --program-id ${state.config.program_id}`:''}`];
 if(state.recorded)commands.push('# This recorded run cannot accept submissions. Start a live local server first.');
 $('worker-command').textContent=commands.join('\n');
}
async function copy(text){await navigator.clipboard.writeText(text);notice('Copied to clipboard.',false);}
$('wallet-button').onclick=()=>{if(wallet.account)wallet.disconnect(api).catch(e=>notice(e.message));else $('wallet-dialog').showModal();};
$('create-button').onclick=()=>openCreate();$('create-form').addEventListener('submit',createBounty);
$('refresh-button').onclick=()=>refresh().catch(e=>notice(e.message));$('job-filter').onchange=renderJobs;
$('copy-worker').onclick=()=>copy($('worker-command').textContent).catch(e=>notice(e.message));
$('copy-evidence').onclick=()=>copy($('evidence-hash').textContent).catch(e=>notice(e.message));
$('download-evidence').onclick=()=>{if(!state.evidence)return;const u=URL.createObjectURL(new Blob([state.evidence.raw],{type:'application/json'})),a=node('a');a.href=u;a.download=`${state.evidence.hash}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);};
$('approve-transaction').onclick=()=>approveTransaction().catch(e=>notice(e.message));
for(const b of document.querySelectorAll('dialog .close'))b.onclick=()=>b.closest('dialog').close();
setInterval(()=>{if(!document.hidden&&state.config&&!state.recorded&&!state.busy&&!document.querySelector('dialog[open]'))refresh().catch(e=>notice(e.message));},5000);
start().catch(e=>notice(e.message));
