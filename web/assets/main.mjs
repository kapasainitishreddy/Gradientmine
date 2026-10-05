import {WalletSession} from './wallet.mjs';
import {bytes,base64,sha256,verifyEnvelope,short,percent,delta,lamports,node,explorer,solToLamports,equal,shellQuote} from './core.mjs';
import {validateIntent,validateWalletSignature} from './wire.mjs';
import {parsePending,recoverPending} from './pending.mjs';

const $=id=>document.getElementById(id),state={config:null,recorded:null,jobs:[],job:null,selected:null,busy:false,evidence:null};
const assetRoot=new URL('./',import.meta.url);
let wallet=null,creationKey=null,pendingAction=null,evidenceRequest=0,detailRequest=0;
wallet=new WalletSession(()=>queueMicrotask(()=>{renderWallet();if(state.job)renderDetail();}));
const label=s=>({AWAITING_FUNDING:'Awaiting escrow',OPEN:'Accepting workers',EVALUATED:'Evaluated · not paid',NO_WINNER:'No eligible winner',SETTLING:'Payout pending',SETTLED:'Payout finalized',REFUNDED:'Refund finalized',ELIGIBLE:'Eligible',REJECTED:'Below threshold',REGISTERED:'Registered',AWAITING_REGISTRATION:'Registration pending'}[s]||s);
const dt=t=>Number.isFinite(t)?new Date(t*1000).toLocaleString(undefined,{timeZoneName:'short'}):'Not recorded';
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
function identifier(value,title='identifier'){
 const box=node('span',null,'identifier'),full=String(value||'Not available');
 const c=button(short(full),()=>{const expanded=c.getAttribute('aria-expanded')==='true';c.textContent=expanded?short(full):full;c.setAttribute('aria-expanded',String(!expanded));},'hash hash-toggle');c.title=full;c.setAttribute('aria-expanded','false');c.setAttribute('aria-label',`Show full ${title}: ${full}`);
 append(box,c,button('Copy',()=>copy(full),'text-button copy-id'));box.lastChild.setAttribute('aria-label',`Copy full ${title}`);return box;
}
function showDialog(id){const dialog=$(id);if(!dialog.open)dialog.showModal();}
function validatorBadge(address){return append(node('div',null,'validator-badge'),node('strong','Trusted validator'),identifier(address,'validator address'),node('p','This named evaluator measures model quality and authorizes payout. Solana enforces escrow, registered recipients and the timeout refund.'));}
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
 const request=++detailRequest;$('detail').setAttribute('aria-busy','true');
 try{
  const result=await api('/api/jobs');if(request!==detailRequest)return;state.jobs=result.jobs;
  state.selected=state.jobs.some(j=>j.id===state.selected)?state.selected:state.jobs[0]?.id||null;
  const job=state.selected?await api(`/api/jobs/${encodeURIComponent(state.selected)}`):null;
  if(request!==detailRequest)return;state.job=job;
  renderJobs();renderDetail();renderCommands();
 }finally{if(request===detailRequest)$('detail').setAttribute('aria-busy','false');}
}
function renderJobs(){
 const filter=$('job-filter').value;
 const jobs=state.jobs.filter(j=>filter==='all'||(filter==='open'?j.state==='OPEN':['EVALUATED','SETTLED','NO_WINNER'].includes(j.state)));
 const items=jobs.map(j=>{
  const b=button('',async()=>{
   const request=++detailRequest;state.selected=j.id;renderJobs();$('detail').setAttribute('aria-busy','true');
   try{const job=state.recorded?j:await api(`/api/jobs/${encodeURIComponent(j.id)}`);if(request!==detailRequest)return;state.job=job;renderDetail();renderCommands();}
   finally{if(request===detailRequest)$('detail').setAttribute('aria-busy','false');}
  },'job');
  b.classList.toggle('selected',state.selected===j.id);b.setAttribute('aria-pressed',String(state.selected===j.id));b.setAttribute('aria-current',String(state.selected===j.id));
  append(b,node('span',label(j.state),'state'),node('strong',j.title),node('small',j.mode==='devnet'?`${lamports(j.policy.reward_lamports)} · Devnet`:'Local · no payment'),node('small',short(j.id)));
  return b;
 });
 $('jobs').replaceChildren(...(items.length?items:[append(node('div',null,'empty'),node('p','No matching bounties.'),node('small',state.recorded?'Change the filter to inspect the recorded run.':'Create the first experiment to get started.'))]));
}
function metric(title,value,detail){return append(node('div',null,'metric'),node('label',title),node('strong',value),node('small',detail));}
function evidenceButton(title,hash,signer=null){const b=button(title,()=>inspect(hash,signer),'text-button');b.disabled=!hash;return b;}
function renderDetail(){
 const root=$('detail'),j=state.job;if(!j){root.replaceChildren(validatorBadge(state.config?.validator),append(node('div',null,'empty'),node('h2','A result starts with a bounty'),node('p','Connect your wallet and define the improvement you want to measure.'),button('Create an experiment',()=>openCreate())));return;}
 const w=j.winner,p=j.policy,subs=j.submissions||[],finished=['EVALUATED','SETTLING','SETTLED','NO_WINNER'].includes(j.state),paid=j.mode==='devnet'&&j.state==='SETTLED'&&!!explorer(j.mode,j.settlement_signature);
 const head=append(node('div',null,'detail-header'),append(node('div'),node('span',j.state==='SETTLED'&&!paid?'Payout evidence unavailable':label(j.state),'state'),node('h2',j.title)),node('span',j.mode==='devnet'?`${lamports(p.reward_lamports)} reward`:'No monetary reward','reward'));
 const trust=validatorBadge(p.validator);
 const meta=append(node('div',null,'detail-meta'),node('span','digits-lora-v1 · Neural classifier'),node('span',`Cutoff: ${dt(p.deadline)}`),node('span',`Minimum: ${delta(p.minimum_delta)}`));
 const pipeline=node('ol',null,'pipeline');pipeline.setAttribute('aria-label','Bounty lifecycle');
 [['Bounty',true],['Escrow',j.mode==='devnet'&&!!explorer(j.mode,j.funding_signature)],['Submitted',subs.length>0],['Registered',subs.some(s=>j.mode==='local'||!!explorer(j.mode,s.registration_signature))],['Evaluated',finished],['Winner',!!w],['Paid',paid]].forEach(([text,done])=>{const stage=append(node('li',null,`stage${done?' done':''}`),node('span',done?'✓':'·','dot'),node('span',text==='Escrow'&&j.mode==='local'?'No escrow':text==='Paid'&&j.mode==='local'?'No payout':text==='Registered'&&j.mode==='local'?'Admitted locally':text));stage.setAttribute('aria-label',`${text}: ${done?'complete':j.mode==='local'&&['Escrow','Paid'].includes(text)?'not applicable':'pending'}`);pipeline.append(stage);});
 const outcome=append(node('div',null,`outcome${paid?' paid':''}`),node('strong',paid?'Selected worker paid · finalized Devnet evidence':w?'Eligible winner selected · not paid':j.state==='REFUNDED'?'Reward refunded · no worker payout':finished?'No eligible winner · not paid':j.state==='AWAITING_FUNDING'?'Awaiting escrow funding · no submissions yet':(j.server_time||Date.now()/1000)>=p.deadline?'Submissions closed · evaluation pending':'Accepting model improvements · not paid'),node('p',w?j.mode==='local'?'This local experiment selected an eligible model. No blockchain funds moved.':paid?'The API checked the finalized payout against the selected, registered worker. Inspect the public transaction below.':'Eligibility is an evaluation decision. Payment remains unconfirmed until exact finalized chain evidence is checked.':'Workers are rewarded for measured improvement over the frozen parent, after the cutoff and eligibility rules.'));
 if(state.recorded)outcome.append(node('p',state.recorded.disclosure,'fine'));
 const metrics=append(node('div',null,'metric-band'),metric('Frozen parent',finished?percent(j.baseline_accuracy):'—','Held-out accuracy'),metric('Best eligible model',w?percent(w.candidate_accuracy):'—',w?(paid?'Registered winner · payout finalized':'Eligible is not the same as paid'):'No eligible result yet'),metric('Measured improvement',w?delta(w.delta):'—',w?`${w.n} held-out examples`:'Scores withheld until cutoff'));
 const table=node('table');const caption=node('caption','Submitted experiments');caption.className='sr-only';
 const thead=node('thead'),hr=node('tr');for(const t of ['Worker','Held-out result','Decision','Evidence']){const th=node('th',t);th.scope='col';hr.append(th);}thead.append(hr);const tbody=node('tbody');
 for(const s of subs){
  const tr=node('tr',null,w?.submission_id===s.id?'winner':null);const who=node('td');append(who,identifier(s.worker,'worker address'),node('small',s.worker_metrics?.negative_control?'Disclosed negative control':`Worker-reported ${s.worker_metrics?.device||'device unknown'}`));
  const result=node('td');append(result,node('strong',s.score?percent(s.score.candidate_accuracy):'Awaiting evaluation'),node('small',s.score?delta(s.score.delta):'No held-out score disclosed'));
  const decision=node('td');append(decision,node('span',w?.submission_id===s.id?(paid?'Winner · paid':'Winner · not paid'):label(s.state),'state'));if(s.score)decision.append(node('small',s.score.reason));
  const evidence=node('td');append(evidence,evidenceButton('Adapter',s.artifact_sha256),evidenceButton('Manifest',s.manifest_sha256,s.worker),s.receipt_sha256?evidenceButton('Receipt',s.receipt_sha256,p.validator):null);const registration=explorer(j.mode,s.registration_signature);if(registration)evidence.append(textLink('Registration ↗',registration));
  append(tr,who,result,decision,evidence);tbody.append(tr);
 }
 if(!subs.length){const tr=node('tr'),td=node('td','No submissions yet. Start a worker using the commands below.');td.colSpan=4;tr.append(td);tbody.append(tr);}
 append(table,caption,thead,tbody);const tableWrap=append(node('div',null,'table-wrap'),table);
 const proof=node('div',null,'proof-note');
 if(w)append(proof,node('strong',`Lower confidence bound: ${delta(w.bootstrap_lower_bound)}`),node('p','Paired bootstrap, one-sided with a predeclared eight-candidate correction. Approximate, IID-dependent evidence. This does not establish resistance to public benchmark leakage.'));
 else append(proof,node('p',finished?'No candidate met the declared improvement and confidence rules. A Devnet refund becomes available after the on-chain timeout.':'The server withholds held-out scores until submission closes. Public validation metrics claimed by workers are not reward eligibility evidence.'));
 const lineage=append(node('section',null,'lineage'),node('h3','Model lineage'));
 const lineagePath=node('div',null,'lineage-path');append(lineagePath,append(node('div',null,'lineage-node'),node('small',p.parent_job_id?'Previous winning model':'Budget-limited parent'),identifier(p.parent_sha256,'parent model hash'),evidenceButton('Inspect parent',p.parent_sha256)));
 if(w)append(lineagePath,node('span','→','lineage-arrow'),append(node('div',null,'lineage-node selected'),node('small','Accepted candidate'),identifier(w.model_sha256,'winning model hash'),evidenceButton('Inspect model',w.model_sha256)));
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
 for(const [name,value] of [['Mode',j.mode==='devnet'?'Solana Devnet':'Local, no on-chain payments'],['Named validator',p.validator],['Policy commitment',j.policy_sha256],['Held-out commitment',p.evaluation_sha256],['Submission cutoff',dt(p.deadline)],['Timeout refund',j.mode==='devnet'?dt(p.refund_after):'Not applicable'],['Creator',j.creator]]){append(dl,node('dt',name),append(node('dd'),['Named validator','Policy commitment','Held-out commitment','Creator'].includes(name)?identifier(value,name.toLowerCase()):code(value)));}
 append(audit,dl,evidenceButton('Inspect immutable policy',j.policy_sha256));
 for(const [name,signature,kind] of [['Funding',j.funding_signature,'tx'],['Payout',j.settlement_signature,'tx'],['Refund',j.refund_signature,'tx'],['Bounty account',j.bounty_address,'address']]){const url=explorer(j.mode,signature,kind);if(url)append(audit,node('p'),textLink(`${name} on Solana Explorer`,url));}
 if(!paid)audit.append(node('p','No finalized payout is claimed for this bounty.','fine'));
 if(j.settlement_warning)audit.append(node('p',`Settlement requires attention: ${j.settlement_warning}`,'form-error'));
 const events=append(node('details',null,'events'),node('summary','Protocol event log'));
 for(const e of j.events||[])events.append(append(node('p'),node('small',dt(e.created)),node('strong',` ${e.kind}`),node('span',` · ${e.message}`)));
 root.replaceChildren(head,trust,meta,pipeline,outcome,metrics,tableWrap,proof,lineage,actions,audit,events);
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
 if(!wallet.account){showDialog('wallet-dialog');return;}
 const f=$('create-form');f.elements.parent.value=parent?.id||'';
 f.elements.reward.disabled=state.config.mode==='local';f.elements.reward.value=state.config.mode==='local'?'0':'0.025';
 $('reward-help').textContent=state.config.mode==='local'?'Local mode has no funds or token payouts. Reward is fixed at zero.':'0.001–1 Devnet SOL. Account rent and transaction fees are shown before wallet approval. Test funds only.';
 $('parent-help').textContent=parent?`Uses the accepted model from “${parent.title}”.`:'Starts from the reproducible, budget-limited digits baseline. Not an LLM or a state-of-the-art baseline.';
 $('create-error').textContent='';creationKey=null;showDialog('create-dialog');
}
async function createBounty(e){
 e.preventDefault();if(state.busy)return;const f=e.target,submit=f.querySelector('[type=submit]');state.busy=true;submit.disabled=true;$('create-error').textContent='';
 try{
  const values={title:f.elements.title.value.trim(),duration_seconds:Number(f.elements.duration.value),reward_lamports:solToLamports(f.elements.reward.value),minimum_delta:Number(f.elements.minimum.value)/100,parent_job_id:f.elements.parent.value||null};
  const encoded=JSON.stringify(values);if(!creationKey||creationKey.body!==encoded)creationKey={body:encoded,key:crypto.randomUUID()};
  const j=await api('/api/jobs',values,{'Idempotency-Key':creationKey.key});state.selected=j.id;$('create-dialog').close();await refresh();notice(j.mode==='devnet'?'Bounty draft created. Use “Fund Devnet escrow” to approve funding in your wallet.':'Local bounty created. Start a worker to submit an actual experiment.',false);
 }catch(err){$('create-error').textContent=err.message;}finally{state.busy=false;submit.disabled=false;}
}
async function mutateJob(action){if(!wallet.account){showDialog('wallet-dialog');return;}notice('Checking protocol state…',false);await api(`/api/jobs/${encodeURIComponent(state.job.id)}/${action}`,{});await refresh();notice('Protocol state refreshed from server evidence.',false);}
async function prepareTransaction(action){
 if(!wallet.account)throw Error('Connect the creator wallet first.');
 const j=await api(`/api/jobs/${encodeURIComponent(state.job.id)}`),intent=await api(`/api/jobs/${encodeURIComponent(j.id)}/transaction`,{action});
 await validateIntent(intent,action,j,state.config,wallet.account.address);
 pendingAction={action,intent,job:j};$('transaction-summary').textContent=action==='fund'?`Escrow ${lamports(j.policy.reward_lamports)} as a test reward.`:'Refund the remaining test reward to the bounty creator.';
 $('transaction-details').textContent=JSON.stringify({action,network:'Solana Devnet',program:intent.program_id,payer:intent.payer,accounts:intent.accounts,reward_lamports:intent.reward_lamports,network_fee_lamports:intent.fee_lamports,account_rent_lamports:intent.rent_lamports,cutoff:dt(j.policy.deadline),refund_after:dt(j.policy.refund_after)},null,2);
 showDialog('transaction-dialog');
}
function pendingKey(id){return `gradientmine.pending.${location.origin}.${id}`;}
function readPending(id){
 try{return parsePending(localStorage.getItem(pendingKey(id)),{jobId:id,origin:location.origin,programId:state.config.program_id});}catch{return null;}
}
async function approveTransaction(){
 const b=$('approve-transaction');b.disabled=true;
 try{
  const p=pendingAction;if(!p)throw Error('No reviewed transaction.');
  if(wallet.account?.address!==p.intent.payer)throw Error('Wallet changed since review. Close this dialog and review the transaction again.');
  // Check persistence before requesting a signature: recovery must survive a lost response or reload.
  const probe=`${pendingKey(p.job.id)}.probe`;localStorage.setItem(probe,'1');localStorage.removeItem(probe);
  const raw=await wallet.sign(p.intent);const signature=await validateWalletSignature(bytes(p.intent.transaction_base64),raw,wallet.account.address);
  if(pendingAction!==p||!$('transaction-dialog').open)throw Error('Transaction review was closed. Nothing was broadcast; review again before approving.');
  const pending={version:1,origin:location.origin,job_id:p.job.id,action:p.action,signature,address:wallet.account.address,program_id:p.intent.program_id,transaction_base64:base64(raw)};localStorage.setItem(pendingKey(p.job.id),JSON.stringify(pending));
  try{await api(`/api/jobs/${encodeURIComponent(p.job.id)}/broadcast`,{action:p.action,transaction_base64:pending.transaction_base64});}
  catch(e){$('transaction-dialog').close();await refresh();throw Error(`${e.message} Signed bytes are retained in this browser. Use “Recheck pending transaction” to check finalization and retry the identical bytes. No payment is assumed.`);}
  $('transaction-dialog').close();await confirmPending(pending);
 }finally{b.disabled=false;}
}
async function confirmPending(p){
 if(!wallet.account)throw Error('Reconnect the same wallet to confirm this transaction.');
 const j=await api(`/api/jobs/${encodeURIComponent(p.job_id)}`);
 if(j.mode!=='devnet'||j.policy.program_id!==state.config.program_id||wallet.account.address!==j.creator||(p.address&&p.address!==wallet.account.address))throw Error('Reconnect the creator wallet on the same Devnet deployment to recover this transaction.');
 notice('Waiting for finalized chain evidence. A broadcast alone is not a payment.',false);
 try{
  await recoverPending(p,api);
  localStorage.removeItem(pendingKey(p.job_id));await refresh();notice('Finalized transaction confirmed against the exact bounty action.',false);
 }
 catch(e){await refresh();throw Error(`${e.message} The original signature and any retained signed bytes remain pending in this browser. Recheck later; an expired transaction needs a fresh review only after checking chain state.`);}
}
async function inspect(hash,signer=null){
 if(!/^[a-f0-9]{64}$/.test(hash||''))throw Error('Invalid artifact reference.');
 const request=++evidenceRequest;
 showDialog('evidence-dialog');$('evidence-title').textContent=signer?'Signed evidence':'Artifact evidence';$('evidence-hash').textContent=hash;$('evidence-json').textContent='';$('evidence-status').textContent='Checking exact bytes…';$('download-evidence').disabled=true;state.evidence=null;
 try{
  const url=state.recorded?new URL(`artifacts/${hash}.json`,assetRoot):`/api/artifacts/${hash}`;
  const r=await fetch(url,{cache:'no-store',signal:AbortSignal.timeout(15000)});if(!r.ok)throw Error('Artifact unavailable. A hash alone does not guarantee storage availability.');
  const raw=new Uint8Array(await r.arrayBuffer());if(raw.length>262144)throw Error('Artifact exceeds the supported limit.');
  if(await sha256(raw)!==hash)throw Error('Artifact SHA-256 mismatch. Do not trust this content.');
  const value=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw));
  if(signer&&!await verifyEnvelope(value,signer))throw Error('Signer or Ed25519 signature verification failed.');
  if(hash===state.job?.policy_sha256&&!equal(value,state.job.policy))throw Error('Policy bytes differ from the displayed bounty.');
  if(request!==evidenceRequest||!$('evidence-dialog').open)return;
  state.evidence={hash,raw};$('evidence-status').textContent=signer?'SHA-256 matches · Ed25519 signature verified against the expected signer.':'SHA-256 matches the referenced exact bytes.';
  $('evidence-json').textContent=JSON.stringify(value,null,2);$('download-evidence').disabled=false;
 }catch(e){if(request===evidenceRequest&&$('evidence-dialog').open)$('evidence-status').textContent=e.message;}
}
function renderCommands(){
 const j=state.job,apiUrl=state.recorded?'http://127.0.0.1:8000':location.origin;
 const commands=['git clone https://github.com/kapasainitishreddy/Gradientmine','cd Gradientmine','python -m venv .venv','# Activate .venv (see README for Windows / macOS / Linux)','python -m pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu','python -m pip install -e ".[chain]"','gradientmine identity --out .local/worker.json',`gradientmine worker --api ${shellQuote(apiUrl)} \\\n  --job ${shellQuote(state.recorded?'YOUR_LIVE_BOUNTY_ID':j?.id||'YOUR_LIVE_BOUNTY_ID')} \\\n  --identity .local/worker.json \\\n  --out ${shellQuote('.local/worker-'+(state.recorded?'YOUR_LIVE_BOUNTY_ID':j?.id||'YOUR_LIVE_BOUNTY_ID'))}${state.config?.mode==='devnet'?` \\\n  --program-id ${shellQuote(state.config.program_id)}`:''}`];
 commands.push('# If interrupted, reuse the same identity and output directory with --resume.');
 if(state.recorded)commands.push('# This recorded run cannot accept submissions. Start a live local server first.');
 $('worker-command').textContent=commands.join('\n');
}
async function copy(text){await navigator.clipboard.writeText(text);notice('Copied to clipboard.',false);}
$('wallet-button').onclick=()=>{if(wallet.account)wallet.disconnect(api).catch(e=>notice(e.message));else showDialog('wallet-dialog');};
$('create-button').onclick=()=>openCreate();$('create-form').addEventListener('submit',createBounty);
$('refresh-button').onclick=()=>refresh().catch(e=>notice(e.message));$('job-filter').onchange=renderJobs;
$('copy-worker').onclick=()=>copy($('worker-command').textContent).catch(e=>notice(e.message));
$('copy-evidence').onclick=()=>copy($('evidence-hash').textContent).catch(e=>notice(e.message));
$('download-evidence').onclick=()=>{if(!state.evidence)return;const u=URL.createObjectURL(new Blob([state.evidence.raw],{type:'application/json'})),a=node('a');a.href=u;a.download=`${state.evidence.hash}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);};
$('approve-transaction').onclick=()=>approveTransaction().catch(e=>notice(e.message));
for(const b of document.querySelectorAll('dialog .close'))b.onclick=()=>b.closest('dialog').close();
$('evidence-dialog').addEventListener('close',()=>{evidenceRequest++;state.evidence=null;$('download-evidence').disabled=true;});
$('transaction-dialog').addEventListener('close',()=>{pendingAction=null;});
for(const dialog of document.querySelectorAll('dialog'))dialog.addEventListener('keydown',event=>{
 if(event.key!=='Tab')return;
 const controls=[...dialog.querySelectorAll('button:not([disabled]), input:not([disabled]):not([type=hidden]), select:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])')].filter(el=>el.getClientRects().length);
 const first=controls[0],last=controls.at(-1);if(!first)return;
 if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
 else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
});
setInterval(()=>{if(!document.hidden&&state.config&&!state.recorded&&!state.busy&&!document.querySelector('dialog[open]'))refresh().catch(e=>notice(e.message));},5000);
start().catch(e=>notice(e.message));
