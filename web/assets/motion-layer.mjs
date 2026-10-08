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
  // Never hide the main headline or sculpture while a remote motion runtime
  // loads. The first contentful paint is always complete and readable.
  const hero=root.querySelectorAll('.hero-kicker,.hero-copy h1 span,.hero-lede,.hero-actions>*');
  if(hero.length)m.animate(hero,{y:[7,0]},{duration:.44,delay:m.stagger(.025),ease});
  const nav=root.querySelectorAll('.topbar .brand,.topbar nav a,.topbar-actions>*');
  if(nav.length)m.animate(nav,{y:[-3,0]},{duration:.3,delay:m.stagger(.02),ease});
  return true;
}
export async function animateDetail(root){
  const m=await runtime();if(!m||!root)return false;
  const sections=root.querySelectorAll('.assurance-panel,.arena,.outcome,.metric-band,.firewall,.passport,.lineage,.audit');
  if(sections.length)m.animate(sections,{opacity:[.94,1],y:[6,0]},{duration:.38,delay:m.stagger(.02),ease});
  const bars=root.querySelectorAll('.arena-bar span');
  for(const bar of bars){
    const width=bar.style.width||'0%';
    m.animate(bar,{width:['0%',width]},{duration:.75,ease});
  }
  const winner=root.querySelector('.arena-winner');
  if(winner)m.animate(winner,{boxShadow:['0 0 0 rgba(123,176,143,0)','0 0 34px rgba(123,176,143,.12)','0 0 0 rgba(123,176,143,0)']},{duration:1.2,ease});
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
  // Native IntersectionObserver in editorial.mjs handles section reveals
  // without hiding the large evidence console during first paint or print.
  return !!root;
}
