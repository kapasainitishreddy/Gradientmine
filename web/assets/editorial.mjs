/* Native, resource-conscious presentation enhancements. Product state, wallet
 * signatures and evidence evaluation remain entirely in their own modules. */
const doc=document;
const menu=doc.getElementById('menu-button');
const nav=doc.getElementById('site-nav');
const reduced=globalThis.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches===true;

if(menu&&nav){
  const setOpen=(open,focus=false)=>{
    menu.setAttribute('aria-expanded',String(open));
    menu.setAttribute('aria-label',open?'Close navigation':'Open navigation');
    nav.dataset.open=String(open);
    if(open&&focus)nav.querySelector('a')?.focus();
  };
  menu.addEventListener('click',()=>{
    setOpen(menu.getAttribute('aria-expanded')!=='true');
  });
  nav.addEventListener('click',event=>{
    if(event.target.closest('a'))setOpen(false);
  });
  doc.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&menu.getAttribute('aria-expanded')==='true'){
      setOpen(false);menu.focus();
    }
  });
  doc.addEventListener('click',event=>{
    if(menu.getAttribute('aria-expanded')==='true'&&
      !menu.contains(event.target)&&!nav.contains(event.target))setOpen(false);
  });
  globalThis.matchMedia?.('(min-width: 761px)')?.addEventListener?.(
    'change',event=>{if(event.matches)setOpen(false);}
  );
}

const header=doc.querySelector('.topbar');
if(header){
  let scheduled=false;
  const update=()=>{
    scheduled=false;
    header.classList.toggle('is-scrolled',globalThis.scrollY>18);
  };
  doc.addEventListener('scroll',()=>{
    if(!scheduled){
      scheduled=true;
      requestAnimationFrame(update);
    }
  },{passive:true});
  update();
}

const stage=doc.querySelector('.sculpture-stage');
if(stage&&globalThis.IntersectionObserver&&!reduced){
  const observer=new IntersectionObserver(entries=>{
    stage.classList.toggle('is-stage-visible',entries.some(entry=>entry.isIntersecting));
  },{rootMargin:'40px'});
  observer.observe(stage);
}
const art=stage?.querySelector('.sculpture-art');
const finePointer=globalThis.matchMedia?.('(hover: hover) and (pointer: fine)')?.matches===true;
if(stage&&art&&!reduced&&finePointer){
  let frame=0,x=0,y=0;
  const paint=()=>{
    frame=0;
    art.style.setProperty('--stage-shift-x',x.toFixed(2)+'px');
    art.style.setProperty('--stage-shift-y',y.toFixed(2)+'px');
  };
  const queue=()=>{if(!frame)frame=requestAnimationFrame(paint);};
  stage.addEventListener('pointermove',event=>{
    const box=stage.getBoundingClientRect();
    x=((event.clientX-box.left)/Math.max(box.width,1)-.5)*8;
    y=((event.clientY-box.top)/Math.max(box.height,1)-.5)*6;
    queue();
  },{passive:true});
  stage.addEventListener('pointerleave',()=>{x=0;y=0;queue();});
  doc.addEventListener('visibilitychange',()=>{
    if(doc.hidden){cancelAnimationFrame(frame);frame=0;}
  });
}

if(!reduced&&globalThis.IntersectionObserver){
  const targets=doc.querySelectorAll(
    '.process-item,.section-intro,.proof-panel,.arena-clarity,'+
    '.trust-grid article,.lab-explainer>div,.lab-workspace-header,.lab-footer-pitch'
  );
  if(targets.length){
    doc.documentElement.classList.add('motion-ready');
    const observer=new IntersectionObserver(entries=>{
      for(const entry of entries){
        if(!entry.isIntersecting)continue;
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    },{threshold:.08,rootMargin:'0px 0px -5% 0px'});
    targets.forEach((node,index)=>{
      node.classList.add('will-reveal');
      node.style.setProperty('--reveal-delay',String(index%4*55)+'ms');
      observer.observe(node);
    });
  }
}
