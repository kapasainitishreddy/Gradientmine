import { METRICS, DEMO_BLUEPRINT, analyzeBlueprint, draftArtifact, candidateLabel } from './bounty-blueprint.mjs';

const form = document.getElementById('bounty-form');
const get = id => document.getElementById(id);
const source = () => {
  const fields = ['name','model','metric','baseline','target','reward','durationDays','candidates','evaluator','candidateResult'];
  const values = Object.fromEntries(fields.map(id => [id, get(id).value]));
  return {...values, rights: get('rights').checked};
};
const setText = (id,text) => {get(id).textContent=String(text);};
const formatValue = (value, unit) => Number.isFinite(value)
  ? Number(value.toFixed(4)).toLocaleString('en-US')+(unit==='%'?'%':' '+unit)
  : '—';
const sol = value => value == null ? '—' : Number(value.toFixed(6)).toLocaleString('en-US')+' SOL';
const errors = get('issues');
const buttonDownload = get('download');
const buttonCopy = get('copy');
let last = null;

function render() {
  last = analyzeBlueprint(source());
  const {spec,issues} = last;
  const unit = spec?.unit || '';
  document.querySelectorAll('.metric-unit').forEach(el=>{el.textContent=unit});
  setText('metric-support',spec ? spec.supported+'. This planning form is not a live escrow service.' : 'Choose a metric.');
  setText('preview-title',last.label || 'A measurable model problem');
  setText('preview-model',last.model || 'Describe the frozen parent model.');
  setText('preview-baseline',formatValue(last.baseline,unit));
  setText('preview-target',formatValue(last.target,unit));
  setText('direction-arrow', spec?.direction==='lower'?'↘':'↗');
  setText('preview-delta',last.delta===null?'—':formatValue(last.delta,unit));
  setText('preview-metric',spec ? spec.label+' · '+spec.supported : 'Choose a metric');
  setText('preview-candidates',Number.isInteger(last.candidates)&&last.candidates>0 ? last.candidates+' candidates' : '—');
  setText('preview-duration',Number.isInteger(last.durationDays)&&last.durationDays>0 ? last.durationDays+' days' : '—');
  setText('preview-evaluator',last.evaluator || '—');
  setText('preview-reward',sol(last.reward));
  setText('preview-fee',sol(last.plannedFee));
  setText('preview-total',sol(last.illustrativeTotal));
  setText('validation-chip',last.ready ? 'DRAFT READY' : 'INCOMPLETE');
  get('validation-chip').classList.toggle('ready',last.ready);
  errors.replaceChildren();
  const list = issues.length ? issues : ['Ready to export an unfunded design draft. Actual independent verification remains undone.'];
  for(const issue of list){const li=document.createElement('li');li.textContent=issue;errors.append(li)}
  setText('candidate-feedback',candidateLabel(last));
  buttonDownload.disabled=!last.ready;
  buttonCopy.disabled=!last.ready;
}

form.addEventListener('input',render);
form.addEventListener('change',render);
form.addEventListener('submit',event=>event.preventDefault());

get('sample').addEventListener('click',()=>{
  for (const [key,value] of Object.entries(DEMO_BLUEPRINT)) {
    const field=get(key);
    if (!field) continue;
    if (key==='rights') field.checked=false; // Never presume ownership or legal consent.
    else field.value=value;
  }
  setText('form-feedback','Example loaded. Confirm your own rights before exporting. No model data is uploaded.');
  render();
  get('name').focus();
});

function artifact() {
  if (!last?.ready) throw new Error('Complete all draft fields first.');
  return JSON.stringify(draftArtifact(source()),null,2)+'\n';
}

buttonDownload.addEventListener('click',()=>{
  try {
    const file=new Blob([artifact()],{type:'application/json'});
    const url=URL.createObjectURL(file);
    const a=document.createElement('a');
    a.href=url;a.download='gradientmine-unfunded-bounty-blueprint.json';
    document.body.append(a);a.click();a.remove();
    URL.revokeObjectURL(url);
    setText('form-feedback','Saved an unfunded planning JSON file. No wallet transaction, upload or payout occurred.');
  } catch(err) {setText('form-feedback',err.message)}
});

buttonCopy.addEventListener('click',async()=>{
  try {
    await navigator.clipboard.writeText(artifact());
    setText('form-feedback','Copied the unfunded planning JSON. No data was submitted.');
  } catch {
    setText('form-feedback','Clipboard unavailable. Use the Download button to save the draft.');
  }
});

render();
