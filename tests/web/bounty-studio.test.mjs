import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {METRICS,DEMO_BLUEPRINT,analyzeBlueprint,draftArtifact,candidateLabel} from '../../web/assets/bounty-blueprint.mjs';

const read = path => readFileSync(new URL(path, import.meta.url),'utf8');

test('buyer blueprint has strict local-only and non-monetary boundaries',()=>{
  const draft=draftArtifact({...DEMO_BLUEPRINT,rights:true},'2026-10-11T12:00:00.000Z');
  assert.equal(draft.status,'UNFUNDED_DESIGN_DRAFT');
  assert.equal(draft.implementation_boundary.not_an_onchain_bounty,true);
  assert.equal(draft.implementation_boundary.not_a_live_model_evaluation,true);
  assert.equal(draft.economics.wallet_connected,false);
  assert.equal(draft.economics.funds_escrowed,false);
  assert.equal(draft.economics.settlement_signature,null);
  assert.equal(draft.economics.current_billing_status,'NOT_IMPLEMENTED');
  assert.equal(draft.evaluation.benchmark_status,'NOT_UPLOADED_OR_VERIFIED');
  assert.equal(draft.created_at,'2026-10-11T12:00:00.000Z');
});

test('numeric scenario enforces baseline, target, unit and planned fee only',()=>{
  const result=analyzeBlueprint({...DEMO_BLUEPRINT,rights:true});
  assert.equal(result.ready,true);
  assert.equal(result.delta,8);
  assert.equal(result.plannedFee,0.2);
  assert.equal(result.illustrativeTotal,2.2);
  assert.equal(result.arithmeticPass,true);
  assert.equal(result.verified,false);
  assert.equal(result.funded,false);
  assert.match(candidateLabel(result),/numeric target ONLY/);
  assert.equal(draftArtifact({...DEMO_BLUEPRINT,rights:true}).economics.hypothetical_fee_rate,0.1);
});

test('requires explicit data-rights acknowledgement and cannot invent it from sample',()=>{
  assert.equal(DEMO_BLUEPRINT.rights,true); // Example preset is an example, never a claim by the user.
  assert.equal(analyzeBlueprint({...DEMO_BLUEPRINT,rights:false}).ready,false);
  assert.throws(()=>draftArtifact({...DEMO_BLUEPRINT,rights:false}),/Complete all validation/);
  assert.match(read('../../web/assets/bounty-ui.mjs'),/field.checked=false/);
});

test('reject missing values, NaN, Infinity, negative reward and unsafe range',()=>{
  const valid={...DEMO_BLUEPRINT,rights:true};
  const cases=[
    {target:'82'},{baseline:''},{target:'NaN'},{target:'Infinity'},
    {reward:'-2'},{reward:'1001'},{candidates:'0'},
    {candidates:'2.5'},{durationDays:'0'},{durationDays:'91'},
    {name:'hi'},{evaluator:'x'},{metric:'surprise'}
  ];
  for(const candidate of cases){
    const result=analyzeBlueprint({...valid,...candidate});
    assert.equal(result.ready,false,JSON.stringify(candidate));
    assert.ok(result.issues.length>=1);
  }
});

test('supports opposite metric directions without presenting an arithmetic pass as verified',()=>{
  const fast={...DEMO_BLUEPRINT,rights:true,metric:'latency',baseline:'400',target:'200',candidateResult:'190'};
  const result=analyzeBlueprint(fast);
  assert.equal(result.ready,true);
  assert.equal(result.spec.direction,'lower');
  assert.equal(result.delta,200);
  assert.equal(result.arithmeticPass,true);
  assert.match(candidateLabel(result),/Still needs held-out evaluation/);
  assert.equal(analyzeBlueprint({...fast,candidateResult:'250'}).arithmeticPass,false);
  assert.equal(analyzeBlueprint({...fast,target:'600'}).ready,false);
  assert.equal(METRICS.cost.supported,'Proposed production task');
});

test('exported user text stays strings; UI uses textContent not unsafe innerHTML',()=>{
  const malicious='<img src=x onerror=alert(1)>';
  const result=draftArtifact({...DEMO_BLUEPRINT,rights:true,name:'bounty '+malicious});
  assert.equal(result.title,'bounty '+malicious);
  const ui=read('../../web/assets/bounty-ui.mjs');
  assert.doesNotMatch(ui,/innerHTML\s*=/);
  assert.match(ui,/\.textContent/);
  assert.match(ui,/URL\.createObjectURL/);
  assert.match(ui,/navigator\.clipboard\.writeText/);
});

test('both judge and bounty pages stay honest and accessible',()=>{
  const index=read('../../web/index.html');
  const studio=read('../../web/bounty.html');
  const judge=read('../../web/judge.html');
  const tour=read('../../web/assets/judge-tour.mjs');
  const css=read('../../web/assets/studio.css');
  assert.match(index,/href="\.\/bounty\.html"/);
  assert.match(index,/href="\.\/judge\.html"/);
  assert.equal(index.split('id="create-button"').length-1,1);
  assert.match(studio,/DESIGN-ONLY · NO WALLET/);
  assert.match(studio,/not a funded bounty/);
  assert.match(studio,/aria-live="polite"/);
  assert.match(studio,/id="rights"/);
  assert.match(studio,/metric-support/);
  assert.match(judge,/data-panel="5"/);
  assert.match(judge,/data-step="5"/);
  assert.match(judge,/No paid customer, live validator service/);
  assert.match(tour,/recorded-run\.json/);
  assert.match(tour,/settlement_signature/);
  assert.match(tour,/if\(!r\.ok\)/);
  assert.doesNotMatch(tour,/innerHTML\s*=/);
  assert.match(css,/@media\(max-width:540px\)/);
  assert.match(css, /prefers-reduced-motion:reduce/);
});
