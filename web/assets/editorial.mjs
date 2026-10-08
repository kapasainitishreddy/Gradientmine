/* Editorial presentation only: mobile navigation and restrained pointer depth.
   All wallet, bounty, artifact and settlement behavior belongs to main.mjs. */
const menu = document.getElementById('menu-button');
const nav = document.getElementById('site-nav');
if (menu && nav) {
  const setOpen = open => {
    menu.setAttribute('aria-expanded', String(open));
    menu.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    nav.dataset.open = String(open);
  };
  menu.addEventListener('click', () => setOpen(menu.getAttribute('aria-expanded') !== 'true'));
  nav.addEventListener('click', event => {
    if (event.target.closest('a')) setOpen(false);
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') {
      setOpen(false); menu.focus();
    }
  });
  document.addEventListener('click', event => {
    if (menu.getAttribute('aria-expanded') === 'true' && !menu.contains(event.target) && !nav.contains(event.target)) setOpen(false);
  });
  const breakpoint = globalThis.matchMedia?.('(min-width: 761px)');
  breakpoint?.addEventListener?.('change', event => { if (event.matches) setOpen(false); });
}

const stage = document.querySelector('.sculpture-stage');
const art = stage?.querySelector('.sculpture-art');
const allowed = globalThis.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches !== true;
const precise = globalThis.matchMedia?.('(hover: hover) and (pointer: fine)')?.matches === true;
if (stage && art && allowed && precise) {
  stage.addEventListener('pointermove', event => {
    const r = stage.getBoundingClientRect();
    const x = ((event.clientX - r.left) / Math.max(r.width, 1) - 0.5) * 12;
    const y = ((event.clientY - r.top) / Math.max(r.height, 1) - 0.5) * 8;
    art.style.setProperty('--stage-shift-x', x.toFixed(2) + 'px');
    art.style.setProperty('--stage-shift-y', y.toFixed(2) + 'px');
  }, {passive: true});
  stage.addEventListener('pointerleave', () => {
    art.style.setProperty('--stage-shift-x', '0px');
    art.style.setProperty('--stage-shift-y', '0px');
  });
}
