export const MOTION_CDN='https://cdn.jsdelivr.net/npm/motion@13.5.0/+esm';
let motionPromise=null;

export function motionAllowed(mediaQuery=globalThis.matchMedia?.('(prefers-reduced-motion: reduce)')){
  return !(mediaQuery && mediaQuery.matches);
}
async function runtime(){
  if(!motionAllowed())return null;
  if(!motionPromise)motionPromise=import(MOTION_CDN).catch(()=>null);
  return motionPromise;
}
const ease=[0.22,1,0.36,1];

export async function animateBoot(root=globalThis.document){
  if(!root)return false;
  if(!motionAllowed()){if(root.documentElement)root.documentElement.dataset.motion='reduced';return false;}
  const m=await runtime();if(!m){if(root.documentElement)root.documentElement.dataset.motion='fallback';return false;}
  if(root.documentElement)root.documentElement.dataset.motion='active';
  const hero=root.querySelectorAll('.hero-kicker,.hero-compact h1,.hero-lede,.hero-actions>*,.hero-proofline>*,.hero-stage-wrap,.mode-banner');
  if(hero.length)m.animate(hero,{opacity:[0,1],y:[16,0],filter:['blur(5px)','blur(0px)']},{duration:.65,delay:m.stagger(.055),ease});
  const nav=root.querySelectorAll('.topbar .brand,.topbar nav a,.topbar-actions>*');
  if(nav.length)m.animate(nav,{opacity:[0,1],y:[-7,0]},{duration:.45,delay:m.stagger(.035),ease});
  return true;
}
export async function animateDetail(root){
  const m=await runtime();if(!m||!root)return false;
  const sections=root.querySelectorAll('.assurance-panel,.arena,.outcome,.metric-band,.firewall,.passport,.lineage,.audit');
  if(sections.length)m.animate(sections,{opacity:[.35,1],y:[12,0],scale:[.993,1]},{duration:.5,delay:m.stagger(.035),ease});
  const bars=root.querySelectorAll('.arena-bar span');
  for(const bar of bars){
    const width=bar.style.width||'0%';
    m.animate(bar,{width:['0%',width]},{duration:.75,ease});
  }
  const winner=root.querySelector('.arena-winner');
  if(winner)m.animate(winner,{boxShadow:['0 0 0 rgba(139,124,246,0)','0 0 34px rgba(139,124,246,.12)','0 0 0 rgba(139,124,246,0)']},{duration:1.2,ease});
  return true;
}
export async function animateThemeChange(target){
  const m=await runtime();if(!m||!target)return false;
  m.animate(target,{scale:[.96,1.04,1],rotate:[0,-1.5,0]},{duration:.34,ease});
  const shell=target.closest?.('.topbar')||globalThis.document?.documentElement;
  if(shell)m.animate(shell,{filter:['saturate(.75)','saturate(1.08)','saturate(1)']},{duration:.45,ease});
  return true;
}
export async function installRevealMotion(root=globalThis.document){
  const m=await runtime();if(!m||!root)return false;
  const targets=root.querySelectorAll('.compact-flow,.workspace,.solver-drawer,.trust');
  for(const el of targets){
    m.inView(el,()=>{m.animate(el,{opacity:[.55,1],y:[18,0]},{duration:.6,ease});},{amount:.18});
  }
  return true;
}
