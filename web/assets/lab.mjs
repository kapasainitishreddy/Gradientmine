/* GradientMine Research Lab: same-origin wallet-authenticated UI.
   All inputs are rendered as text, never interpreted as HTML or executable code. */
import {WalletSession} from './wallet.mjs';
import {base64, equal, sha256, verifyEnvelope} from './core.mjs';
import {canonicalJson} from './lab-canonical.mjs';

const $ = id => document.getElementById(id);
const encoder = new TextEncoder();
const state = {online:false, types:null, workspaces:[], list:[], selected:null, detail:null, busy:false};
let wallet;
const n = (tag, content, className) => {
  const element = document.createElement(tag);
  if (content != null) element.textContent = String(content);
  if (className) element.className = className;
  return element;
};
const stable = canonicalJson;
function status(message, bad=false) {
  const x=$('lab-status');
  x.textContent=message;
  x.dataset.bad=String(bad);
}
async function api(path, payload, {anonymous=false}={}) {
  const headers = {'Accept':'application/json'};
  if (payload !== undefined) headers['Content-Type']='application/json';
  if (wallet?.token && !anonymous) headers.Authorization='Bearer '+wallet.token;
  const response = await fetch(path, {
    method:payload===undefined?'GET':'POST', headers,
    body:payload===undefined?undefined:JSON.stringify(payload), redirect:'error',
    credentials:'same-origin', cache:'no-store',
  });
  const mime = response.headers.get('content-type')||'';
  if (!mime.includes('application/json')) throw Error('Research API unavailable on this static deployment');
  const data=await response.json();
  if (!response.ok) throw Error(data.error||'Research API error '+response.status);
  return data;
}
async function safe(action) {
  if (state.busy) return;
  state.busy=true;
  $('lab-status').setAttribute('aria-busy','true');
  updateControls();
  try {await action();}
  catch(error){status(String(error.message||error),true);}
  finally {
    state.busy=false;
    $('lab-status').setAttribute('aria-busy','false');
    updateControls();
  }
}
async function sign(payload) {
  if (!wallet?.account || !wallet?.wallet) throw Error('Connect a wallet first');
  const bytes=encoder.encode(stable(payload));
  const account=wallet.account;
  const signMessage=wallet.wallet.features['solana:signMessage'].signMessage;
  const [signed]=await signMessage({account,message:bytes});
  if (wallet.account!==account || !wallet.token || !equal([...signed.signedMessage],[...bytes])) {
    throw Error('Wallet or signed message changed. Reconnect and retry.');
  }
  return {
    payload,
    payload_base64:base64(bytes),
    signer:wallet.account.address,
    signature:base64(signed.signature),
  };
}
wallet=new WalletSession(()=>{renderWallet();updateControls();});

function renderWallet() {
  $('lab-wallet').textContent=wallet?.account?wallet.account.address.slice(0,6)+'… Disconnect':'Connect wallet';
  const list=$('lab-wallet-list');
  if (!list || !wallet) return;
  list.replaceChildren();
  for (const item of wallet.wallets) {
    const button=n('button',item.name||'Solana wallet','lab-button');
    button.type='button';
    button.addEventListener('click',()=>safe(async()=>{
      await wallet.connect(item,api);
      $('lab-wallet-dialog').close();
      status('Wallet authenticated; no funds moved.');
      await refreshAll();
    }));
    list.append(button);
  }
  if (!wallet.wallets.size) list.append(n('p','No compatible Wallet Standard wallet found. Open in a browser with an enabled Solana wallet.'));
}
$('lab-wallet').addEventListener('click',()=>safe(async()=>{
  if (!state.online) throw Error('Public static viewer is read-only. Start the private FastAPI service.');
  if (wallet.account) {
    await wallet.disconnect(api);
    state.workspaces=[];state.selected=null;state.detail=null;
    await refreshAll();
    return;
  }
  renderWallet();$('lab-wallet-dialog').showModal();
}));
$('lab-wallet-close').addEventListener('click',()=>$('lab-wallet-dialog').close());

function currentWorkspace() {
  return state.workspaces.find(ws => ws.id === $('lab-workspace-select').value);
}
function updateControls(){
  const connected=!!wallet?.account && state.online && !state.busy;
  const active=currentWorkspace();
  const canCreate=connected && !!active && ['owner','researcher'].includes(active.role);
  const canInvite=connected && active?.role==='owner';
  const selected=state.detail;
  const canSubmit=connected && selected?.state==='OPEN';
  const canEvaluate=connected && selected?.state==='OPEN' && Date.now()/1000 >= selected.policy.deadline;
  const canReview=connected && !!selected?.result_sha256 && !!active &&
    ['owner','reviewer'].includes(active.role) && selected.workspace_id===active.id;
  for(const id of ['lab-workspace-name','lab-workspace-select'])$(id).disabled=!connected;
  for(const id of ['lab-title','lab-kind','lab-visibility','lab-duration','lab-delta','lab-docs','lab-dev','lab-holdout'])$(id).disabled=!canCreate;
  $('lab-artifact').disabled=!canSubmit;
  $('lab-submit').disabled=!canSubmit;
  $('lab-evaluate').disabled=!canEvaluate;
  $('lab-review').disabled=!canReview;
  $('lab-member-address').disabled=!canInvite;
  $('lab-member-role').disabled=!canInvite;
  $('lab-download').disabled=!selected;
  $('lab-workspace-form').querySelector('button[type="submit"]').disabled=!connected;
  $('lab-invite-form').querySelector('button[type="submit"]').disabled=!canInvite;
  $('lab-create-form').querySelector('button[type="submit"]').disabled=!canCreate;
}
async function refreshWorkspaceSecurity() {
  const members=$('lab-members'),audit=$('lab-audit');
  if (!members || !audit) return;
  members.replaceChildren();audit.replaceChildren();
  const active=currentWorkspace();
  if (!wallet?.account || !state.online || !active) {
    members.append(n('p','Connect a wallet and select an owned workspace.'));
    audit.append(n('p','Audit events are available to authorized workspace members.'));
    return;
  }
  if (active.role === 'owner') {
    const result=await api('/api/lab/workspaces/'+encodeURIComponent(active.id)+'/members');
    for(const item of result.members||[]) {
      const row=n('div',null,'lab-member-row');
      const identity=n('div');
      identity.append(n('strong',item.address.slice(0,7)+'…'+item.address.slice(-6)),
                      n('span',item.role));
      row.append(identity);
      if (item.role!=='owner') {
        const revoke=n('button','Revoke','lab-secondary lab-revoke');
        revoke.type='button';
        revoke.setAttribute('aria-label','Revoke member '+item.address);
        revoke.addEventListener('click',()=>safe(async()=>{
          if (!window.confirm('Revoke this wallet’s access to the workspace?')) return;
          await api('/api/lab/workspaces/'+encodeURIComponent(active.id)+
            '/members/'+encodeURIComponent(item.address)+'/revoke',{});
          await refreshAll();
          status('Member access revoked and recorded in the workspace audit log.');
        }));
        row.append(revoke);
      }
      members.append(row);
    }
  } else {
    members.append(n('p','Only workspace owners can view and manage the member roster.'));
  }
  if (['owner','reviewer'].includes(active.role)) {
    const result=await api('/api/lab/workspaces/'+encodeURIComponent(active.id)+'/audit');
    if (!result.events?.length) audit.append(n('p','No events recorded yet.'));
    for (const event of result.events||[]) {
      const row=n('div',null,'lab-audit-row');
      row.append(n('strong',event.kind.replaceAll('_',' ')),
                 n('span',event.actor.slice(0,7)+'… · '+new Date(event.created_at*1000).toLocaleString()));
      audit.append(row);
    }
  } else {
    audit.append(n('p','Audit history is available to owners and reviewers.'));
  }
}
async function refreshAll(){
  if (!state.online) return;
  if (wallet?.account) {
    const workspaces=(await api('/api/lab/workspaces')).workspaces||[];
    state.workspaces=workspaces;
    const selector=$('lab-workspace-select'),selected=selector.value;
    selector.replaceChildren(n('option','Select a workspace'));
    selector.firstElementChild.value='';
    for(const ws of workspaces){
      const option=n('option',ws.name+' · '+ws.role);
      option.value=ws.id;selector.append(option);
    }
    if (workspaces.length) selector.value=workspaces.some(x=>x.id===selected)?selected:workspaces[0].id;
  } else {
    state.workspaces=[];
    const selector=$('lab-workspace-select');
    selector.replaceChildren(n('option','Connect wallet to view workspaces'));
    selector.firstElementChild.value='';
  }
  const result=await api('/api/lab/benchmarks',undefined,{anonymous:!wallet?.account});
  state.list=result.benchmarks||[];
  if (!state.list.find(x=>x.id===state.selected)) state.selected=state.list[0]?.id||null;
  renderList();
  await loadDetail();
  await refreshWorkspaceSecurity();
  updateControls();
}
function renderList(){
  const target=$('lab-benchmarks');target.replaceChildren();
  if (!state.list.length) {
    target.append(n('p',wallet?.account?'No benchmarks yet. Create a workspace and start one.':'No public competitions on this operator.'));
    return;
  }
  for(const item of state.list){
    const button=n('button',null,'lab-benchmark-button');
    button.type='button';
    button.setAttribute('aria-pressed',String(state.selected===item.id));
    button.append(n('span',item.kind.replaceAll('_',' ').toUpperCase()+' / '+item.visibility,'lab-benchmark-type'),
                  n('strong',item.title),
                  n('span',item.state+' · '+item.mode,'lab-benchmark-state'));
    button.addEventListener('click',()=>safe(async()=>{state.selected=item.id;renderList();await loadDetail();}));
    target.append(button);
  }
}
async function loadDetail(){
  const target=$('lab-detail');target.replaceChildren();
  if (!state.selected){
    state.detail=null;state.loadedTemplateFor=null;
    target.append(n('p','Select or create a competition to inspect evidence.'));
    updateControls();return;
  }
  const item=await api('/api/lab/benchmarks/'+encodeURIComponent(state.selected));
  state.detail=item;
  if (state.loadedTemplateFor!==item.id) {
    const choice=defaults[item.kind];
    $('lab-artifact').value=choice?JSON.stringify(choice,null,2):'';
    state.loadedTemplateFor=item.id;
  }
  target.append(n('span',item.state+' / '+item.kind.toUpperCase(),'lab-detail-kicker'));
  target.append(n('h3',item.title));
  target.append(n('p','Frozen policy: '+item.policy_sha256,'lab-hash'));
  target.append(n('p','Private set commitment: '+item.policy.evaluation_sha256,'lab-hash'));
  target.append(n('p','Minimum improvement: '+(100*item.policy.minimum_delta).toFixed(2)+'% · Max submissions '+item.policy.max_candidates));
  target.append(n('p','Deadline: '+new Date(item.policy.deadline*1000).toLocaleString()));
  target.append(n('p','Held-out examples remain encrypted and undisclosed until evaluator execution. Signed receipts describe outcomes, not cryptographic proof of model quality.'));
  const entries=n('div',null,'lab-entries');
  entries.append(n('h4','Submitted candidates · '+item.entries.length));
  if (!item.entries.length) entries.append(n('p','No candidates yet.'));
  for(const e of item.entries){
    const row=n('div',null,'lab-entry');
    row.append(n('strong',e.worker.slice(0,7)+'…'+e.worker.slice(-5)));
    row.append(n('span',e.state+' · '+e.artifact_sha256.slice(0,14)+'…'));
    if(e.score){
      const ratio=Number(e.score.candidate_accuracy);
      row.append(n('span','Quality '+(100*ratio).toFixed(2)+'% · '+(e.score.eligible?'Eligible':'Ineligible')));
      const meter=n('div',null,'lab-score-track');
      meter.setAttribute('role','meter');
      meter.setAttribute('aria-label','Verified held-out success rate');
      meter.setAttribute('aria-valuemin','0');
      meter.setAttribute('aria-valuemax','100');
      meter.setAttribute('aria-valuenow',String(Math.round(100*ratio)));
      const fill=n('span');
      fill.style.width=(100*Math.max(0,Math.min(1,ratio))).toFixed(1)+'%';
      meter.append(fill);
      row.append(meter);
    }
    if(e.receipt){
      const ok=await verifyEnvelope(e.receipt,item.policy.validator);
      row.append(n('span',ok?'✓ Named evaluator signature verified':'⚠ Receipt verification failed','lab-evidence-verify'));
    }
    entries.append(row);
  }
  target.append(entries);
  if(item.winner) target.append(n('p','Selected winner: '+item.winner.worker+' · '+item.winner.artifact_sha256,'lab-winner'));
  if(item.state==='NO_WINNER') target.append(n('p','No candidate cleared the frozen eligibility requirement.'));
  target.append(n('p','Settlement: none. This research competition has zero monetary reward.','lab-settlement'));
  renderList();
  updateControls();
}

$('lab-refresh').addEventListener('click',()=>safe(async()=>{await refreshAll();status('Competition evidence refreshed.');}));
$('lab-workspace-form').addEventListener('submit',event=>{
  event.preventDefault();
  safe(async()=>{
    const name=$('lab-workspace-name').value;
    const item=await api('/api/lab/workspaces',{name,kind:'team'});
    $('lab-workspace-name').value='';
    await refreshAll();
    $('lab-workspace-select').value=item.id;
    updateControls();
    status('Workspace created. Ownership belongs to the authenticated wallet.');
  });
});
$('lab-invite-form').addEventListener('submit',event=>{
  event.preventDefault();
  safe(async()=>{
    const id=$('lab-workspace-select').value;
    if(!id)throw Error('Select a workspace');
    await api('/api/lab/workspaces/'+encodeURIComponent(id)+'/members',{
      address:$('lab-member-address').value.trim(),role:$('lab-member-role').value,
    });
    $('lab-member-address').value='';
    await refreshWorkspaceSecurity();
    status('Membership updated and recorded. No organization email or billing was created.');
  });
});
$('lab-workspace-select').addEventListener('change',()=>safe(async()=>{
  updateControls();
  await refreshWorkspaceSecurity();
}));
$('lab-load-sample').addEventListener('click',()=>{
  const kind=$('lab-kind').value;
  const documents=[{id:'a',title:'Application platform',text:'Applications can be hosted on managed compute platforms.'},
                   {id:'b',title:'Animal care',text:'Veterinarians care for domestic animals.'},
                   {id:'c',title:'Local archive',text:'Local historical records are archived securely.'}];
  let development,holdout;
  if(kind==='safety_refusal'){
    development=[{prompt:'prohibited request',should_refuse:true},{prompt:'ordinary request',should_refuse:false}];
    holdout=Array.from({length:40},(_,i)=>({prompt:(i%2?'ordinary':'prohibited')+' synthetic case '+i,should_refuse:i%2===0}));
  }else if(kind==='llm_prompt'){
    development=[{question:'What does the application platform host?',answer:'Applications'},{question:'Who cares for domestic animals?',answer:'Veterinarians'}];
    holdout=Array.from({length:12},(_,i)=>({question:i%2?'Who cares for animals?':'What can be hosted?',answer:i%2?'Veterinarians':'Applications'}));
  }else if(kind==='grounded_qa'){
    development=[{question:'Who cares for domestic animals?',answer:'Veterinarians',relevant_ids:['b']},{question:'Where are historical records?',answer:'archives',relevant_ids:['c']}];
    holdout=Array.from({length:40},(_,i)=>({question:i%2?'Who cares for domestic animals?':'Where are historical records?',answer:i%2?'Veterinarians':'archives',relevant_ids:[i%2?'b':'c']}));
  }else{
    development=[{query:'application',relevant_ids:['a']},{query:'animals',relevant_ids:['b']}];
    holdout=Array.from({length:40},(_,i)=>({query:i%2?'animals example '+i:'application example '+i,relevant_ids:[i%2?'b':'a']}));
  }
  $('lab-docs').value=JSON.stringify(documents,null,2);
  $('lab-dev').value=JSON.stringify(development,null,2);
  $('lab-holdout').value=JSON.stringify(holdout,null,2);
  status('Synthetic example loaded. These are demonstration examples, not confidential commercial benchmarks.');
});
const defaults={
  retrieval:{format:'gradientmine.retrieval.v1',top_k:2,title_boost:2,expansion:{}},
  grounded_qa:{format:'gradientmine.grounded_qa.v1',top_k:2,title_boost:2,min_overlap:1,expansion:{}},
  safety_refusal:{format:'gradientmine.safety_policy.v1',block_terms:['prohibited'],allow_terms:[]},
  efficiency:{format:'gradientmine.efficiency.v1',top_k:1,title_boost:1,max_docs:3},
  llm_prompt:{format:'gradientmine.prompt_template.v1',template:'Use these facts: {context}\nQuestion: {question}\nAnswer:',max_new_tokens:64},
};
$('lab-kind').addEventListener('change',()=>{
  $('lab-artifact').value=JSON.stringify(defaults[$('lab-kind').value],null,2);
});
$('lab-kind').dispatchEvent(new Event('change'));

$('lab-create-form').addEventListener('submit',event=>{
  event.preventDefault();
  safe(async()=>{
    if(!state.online||!wallet.account)throw Error('Connect your wallet to the live private backend');
    const payload={
      workspace_id:$('lab-workspace-select').value,
      title:$('lab-title').value,
      kind:$('lab-kind').value,visibility:$('lab-visibility').value,
      duration_seconds:Number($('lab-duration').value),
      minimum_delta:Number($('lab-delta').value),
      documents:JSON.parse($('lab-docs').value),
      development:JSON.parse($('lab-dev').value),
      holdout:JSON.parse($('lab-holdout').value),
    };
    const created=await api('/api/lab/benchmarks',payload);
    state.selected=created.id;
    await refreshAll();
    status('Immutable benchmark created with encrypted private examples.');
  });
});
$('lab-submit').addEventListener('click',()=>safe(async()=>{
  if(!state.detail||!wallet?.account)throw Error('Select a competition and connect a wallet');
  const artifact=JSON.parse($('lab-artifact').value);
  if (state.detail.state!=='OPEN') throw Error('This competition is no longer accepting submissions.');
  const hash=await sha256(encoder.encode(stable(artifact)));
  const claim={
    format:'gradientmine.lab-submission.v1',
    benchmark_id:state.detail.id,
    policy_sha256:state.detail.policy_sha256,
    artifact_sha256:hash,
    submitted_at:Math.floor(Date.now()/1000),
  };
  const manifest=await sign(claim);
  await api('/api/lab/benchmarks/'+encodeURIComponent(state.detail.id)+'/submissions',{artifact,manifest});
  await refreshAll();
  status('Candidate signed and registered. Private scores stay sealed until cutoff.');
}));
$('lab-evaluate').addEventListener('click',()=>safe(async()=>{
  if(!state.detail)throw Error('Choose a competition');
  if (Date.now()/1000 < state.detail.policy.deadline) throw Error('The benchmark is still accepting candidates.');
  await api('/api/lab/benchmarks/'+encodeURIComponent(state.detail.id)+'/evaluate',{});
  await refreshAll();
  status('Evaluator results and signed receipts are available.');
}));
$('lab-review').addEventListener('click',()=>safe(async()=>{
  const d=state.detail;
  if(!d?.result_sha256)throw Error('Evaluation must be completed before a review');
  const claim={
    format:'gradientmine.review.v1',
    benchmark_id:d.id,policy_sha256:d.policy_sha256,results_sha256:d.result_sha256,
  };
  const envelope=await sign(claim);
  await api('/api/lab/benchmarks/'+encodeURIComponent(d.id)+'/reviews',{envelope});
  await refreshAll();
  status('Signed result-hash attestation saved. This is not independent evaluator consensus.');
}));
$('lab-download').addEventListener('click',()=>{
  if(!state.detail)return;
  const filename='gradientmine-lab-'+state.detail.id+'.json';
  const blob=new Blob([JSON.stringify(state.detail,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob);
  const link=n('a');
  link.href=url;link.download=filename;link.click();
  setTimeout(()=>URL.revokeObjectURL(url),200);
});
async function start(){
  try{
    state.types=await api('/api/lab/types',undefined,{anonymous:true});
    if(!state.types.enabled||state.types.mode!=='local-research')throw Error('Unsupported research backend');
    state.online=true;
    $('lab-mode').textContent='PRIVATE OPERATOR CONNECTED · LOCAL RESEARCH · ZERO PAYMENT';
    await refreshAll();
    status('Research Lab connected. Wallet authentication is required to create a workspace.');
  }catch(e){
    state.online=false;
    $('lab-mode').textContent='STATIC SHOWCASE · PRIVATE RESEARCH API NOT DEPLOYED';
    status('The research backend is not available at this public Pages origin. Run the API locally to use competitions.',true);
  }finally{renderWallet();updateControls();}
}
start();
