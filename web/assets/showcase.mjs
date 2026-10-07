const finite=v=>typeof v==='number'&&Number.isFinite(v);
export function formatScore(v){return finite(v)?(v*100).toFixed(2):'—';}
export function showcaseModel(job={}){
  const winner=job.winner||null;
  const subs=Array.isArray(job.submissions)?job.submissions:[];
  const paid=job.mode==='devnet'&&job.state==='SETTLED'&&typeof job.settlement_signature==='string'&&job.settlement_signature.length>0;
  return {
    parent:finite(job.baseline_accuracy)?job.baseline_accuracy:null,
    winner:finite(winner?.candidate_accuracy)?winner.candidate_accuracy:null,
    delta:finite(winner?.delta)?winner.delta:null,
    lowerBound:finite(winner?.bootstrap_lower_bound)?winner.bootstrap_lower_bound:null,
    examples:Number.isInteger(winner?.n)?winner.n:null,
    paid,
    networkLabel:job.mode==='devnet'?'DEVNET':'LOCAL EVIDENCE',
    workers:subs.map(s=>({
      worker:s.worker||null,
      development:finite(s?.worker_metrics?.public_validation_accuracy)?s.worker_metrics.public_validation_accuracy:null,
      assurance:finite(s?.score?.candidate_accuracy)?s.score.candidate_accuracy:null,
      eligible:s?.score?.eligible===true,
      winner:winner?.submission_id!=null&&s.id===winner.submission_id,
      negativeControl:s?.worker_metrics?.negative_control===true,
      status:s?.score==null?'SEALED':(winner?.submission_id!=null&&s.id===winner.submission_id?'WINNER':(s?.score?.eligible===true?'ELIGIBLE':'REJECTED'))
    }))
  };
}

const clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const lerp=(a,b,t)=>a+(b-a)*t;
const hexToRgba=(hex,alpha=1)=>{
  const value=String(hex||'').trim();
  if(!/^#[0-9a-f]{6}$/i.test(value))return `rgba(139,124,246,${alpha})`;
  const n=parseInt(value.slice(1),16);
  return `rgba(${(n>>16)&255},${(n>>8)&255},${n&255},${alpha})`;
};
function palette(doc){
  const s=getComputedStyle(doc.documentElement);
  return {
    text:s.getPropertyValue('--text').trim()||'#f7f7fa',
    muted:s.getPropertyValue('--muted').trim()||'#a8a8b7',
    line:s.getPropertyValue('--line').trim()||'#303039',
    accent:s.getPropertyValue('--accent-bg').trim()||'#8b7cf6',
    good:s.getPropertyValue('--good').trim()||'#95e6bf',
    bad:s.getPropertyValue('--bad').trim()||'#ff9fab',
    surface:s.getPropertyValue('--surface').trim()||'#111116'
  };
}
function curvePoint(a,b,t,bend=0){
  const mx=(a.x+b.x)/2,my=(a.y+b.y)/2+bend;
  const u=1-t;
  return {x:u*u*a.x+2*u*t*mx+t*t*b.x,y:u*u*a.y+2*u*t*my+t*t*b.y};
}
export function createShowcase(doc=globalThis.document){
  const canvas=doc?.getElementById?.('proof-canvas');
  if(!canvas)return {update(){},destroy(){}};
  const ctx=canvas.getContext('2d');
  const stage=canvas.closest('.hero-stage,.proof-stage');
  const reduced=globalThis.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches===true;
  let model=showcaseModel({});
  let raf=0,start=performance.now(),width=1,height=1,dpr=1,pointer={x:.5,y:.5};
  let observer=null;

  function resize(){
    const rect=canvas.getBoundingClientRect();
    dpr=Math.min(2,globalThis.devicePixelRatio||1);
    width=Math.max(1,rect.width);height=Math.max(1,rect.height);
    canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
  }
  function text(str,x,y,size,color,align='left',weight=600){
    ctx.fillStyle=color;ctx.font=`${weight} ${size}px ui-monospace,SFMono-Regular,Consolas,monospace`;ctx.textAlign=align;ctx.textBaseline='middle';ctx.fillText(str,x,y);
  }
  function node(p,r,label,value,color,glow=0){
    if(glow){ctx.shadowColor=color;ctx.shadowBlur=glow;}
    ctx.fillStyle=hexToRgba(color,.12);ctx.strokeStyle=hexToRgba(color,.75);ctx.lineWidth=1.2;
    ctx.beginPath();ctx.arc(p.x,p.y,r,0,Math.PI*2);ctx.fill();ctx.stroke();ctx.shadowBlur=0;
    text(label,p.x,p.y-r-13,9,hexToRgba(color,.9),'center',700);
    text(value,p.x,p.y+1,12,color,'center',700);
  }
  function line(a,b,color,alpha=.35,bend=0){
    const mid=curvePoint(a,b,.5,bend);
    ctx.strokeStyle=hexToRgba(color,alpha);ctx.lineWidth=1;
    ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.quadraticCurveTo(mid.x,mid.y,b.x,b.y);ctx.stroke();
  }
  function packet(a,b,t,color,bend=0){
    const p=curvePoint(a,b,t,bend);
    ctx.fillStyle=color;ctx.shadowColor=color;ctx.shadowBlur=10;
    ctx.beginPath();ctx.arc(p.x,p.y,2.4,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
  }
  function render(now){
    const p=palette(doc),t=(now-start)/1000;
    ctx.clearRect(0,0,width,height);
    const ox=(pointer.x-.5)*8,oy=(pointer.y-.5)*5;
    const parent={x:width*.10+ox,y:height*.52+oy};
    const workerX=width*.34+ox*.55;
    const workers=[{x:workerX,y:height*.25+oy*.3},{x:workerX,y:height*.52+oy*.3},{x:workerX,y:height*.78+oy*.3}];
    const gate={x:width*.63+ox*.2,y:height*.52};
    const final={x:width*.87,y:height*.52};

    // subtle background field
    for(let i=0;i<26;i++){
      const x=((i*97)%100)/100*width,y=((i*53)%97)/97*height;
      const pulse=.025+.018*Math.sin(t*0.8+i);
      ctx.fillStyle=hexToRgba(p.accent,pulse);
      ctx.fillRect(x,y,1.2,1.2);
    }

    // section labels
    text('FROZEN PARENT',parent.x,20,9,p.muted,'center',700);
    text('WORKER FIELD',workerX,20,9,p.muted,'center',700);
    text('ASSURANCE GATE',gate.x,20,9,p.muted,'center',700);
    text(model.paid?'SETTLED':'SELECTED MODEL',final.x,20,9,p.muted,'center',700);

    workers.forEach((w,i)=>line(parent,w,p.accent,.25,(i-1)*18));
    workers.forEach((w,i)=>line(w,gate,i===2?p.bad:p.good,i===2?.16:.25,(i-1)*12));
    line(gate,final,p.accent,.45,0);

    if(!reduced){
      for(let i=0;i<workers.length;i++){
        const phase=(t*.16+i*.23)%1;
        packet(parent,workers[i],phase,p.accent,(i-1)*18);
        packet(workers[i],gate,(phase+.34)%1,i===2?p.bad:p.good,(i-1)*12);
      }
      packet(gate,final,(t*.18+.12)%1,p.accent);
    }

    const workerModels=model.workers.slice(0,3);
    node(parent,21,'BASE',formatScore(model.parent),p.accent,8);
    workers.forEach((w,i)=>{
      const wm=workerModels[i];
      const color=wm?.winner?p.accent:(wm?.eligible?p.good:(wm?.negativeControl?p.bad:p.muted));
      node(w,17,wm?.negativeControl?'NEG CTRL':`W${i+1}`,formatScore(wm?.assurance),color,wm?.winner?12:0);
      text(wm?.status||'SEALED',w.x,w.y+31,8,color,'center',700);
    });
    node(gate,24,'VALIDATOR',model.lowerBound==null?'SEALED':`LCB +${formatScore(model.lowerBound)}`,p.good,8);
    node(final,26,'WINNER',formatScore(model.winner),p.accent,14);
    if(model.delta!=null)text(`Δ +${formatScore(model.delta)} pp`,final.x,final.y+40,10,p.good,'center',700);

    if(!reduced)raf=requestAnimationFrame(render);
  }
  function update(job){
    model=showcaseModel(job||{});
    const summary=doc.getElementById('proof-summary');
    if(summary){
      const winner=model.winner==null?'No winner yet':`${formatScore(model.parent)} → ${formatScore(model.winner)} · +${formatScore(model.delta)} pp`;
      summary.textContent=`${winner} · ${model.examples??'—'} held-out · ${model.networkLabel} · ${model.paid?'finalized payout':'no payout claimed'}`;
    }
    if(reduced)render(performance.now());
  }
  function onPointer(e){
    const r=stage?.getBoundingClientRect?.();if(!r)return;
    pointer.x=clamp((e.clientX-r.left)/Math.max(1,r.width),0,1);
    pointer.y=clamp((e.clientY-r.top)/Math.max(1,r.height),0,1);
  }
  resize();
  globalThis.addEventListener?.('resize',resize,{passive:true});
  stage?.addEventListener?.('pointermove',onPointer,{passive:true});
  if(globalThis.ResizeObserver){observer=new ResizeObserver(resize);observer.observe(canvas);}
  if(reduced)render(performance.now());else raf=requestAnimationFrame(render);
  return {update,destroy(){cancelAnimationFrame(raf);observer?.disconnect();globalThis.removeEventListener?.('resize',resize);stage?.removeEventListener?.('pointermove',onPointer);}};
}
