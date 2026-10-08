import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const read = file => readFileSync(new URL(file, import.meta.url), 'utf8');
const html = read('../../web/index.html');
const css = read('../../web/assets/editorial.css');
const logic = read('../../web/assets/editorial.mjs');
const art = read('../../web/assets/transformation.svg');

test('editorial homepage ships an honest hero and museum-style proof exhibit', () => {
  assert.match(html, /DON'T<\/span><span>GUESS\.<\/span><span class="hero-emphasis">PROVE IT\./);
  assert.match(html, /id="hero-title" aria-label="Don't guess\. Prove it\."/);
  assert.match(html, /84\.72/);
  assert.match(html, /95\.28/);
  assert.match(html, /360 HELD-OUT EXAMPLES/);
  assert.match(html, /NO ON-CHAIN PAYOUT/);
  assert.match(html, /recorded local experiment/i);
  assert.match(html, /id="the-proof"/);
  assert.match(html, /id="arena"/);
  assert.match(html, /id="how-it-works"/);
});

test('editorial build preserves all dynamic API/wallet/evidence hooks exactly once', () => {
  const required = [
    'wallet-button','create-button','jobs','detail','job-filter','mode-banner',
    'notice','proof-canvas','proof-summary','worker-command','copy-worker',
    'refresh-button','wallet-list','wallet-dialog','create-dialog','create-form',
    'reward-help','parent-help','create-error','transaction-dialog',
    'transaction-summary','transaction-details','approve-transaction',
    'evidence-dialog','evidence-title','evidence-status','evidence-hash',
    'evidence-json','download-evidence','copy-evidence',
  ];
  for (const id of required) {
    assert.equal(html.split('id="' + id + '"').length - 1, 1, 'missing or duplicate #' + id);
  }
});

test('site only advertises the documented modes and real evidence', () => {
  assert.doesNotMatch(html, /(?:\$\d[\d,]*|registered builders|active real money bounties|verified live payout)/i);
  assert.match(html, /NO ON-CHAIN PAYOUT/);
  assert.match(html, /read-only|recorded local/i);
  assert.match(html, /the named evaluator/i);
});

test('mobile menu is keyboard-operated; reduced-motion and breakpoint styles exist', () => {
  assert.match(html, /id="menu-button"[^>]*aria-controls="site-nav"[^>]*aria-expanded="false"/);
  assert.match(logic, /menu\.addEventListener\('click'/);
  assert.match(logic, /event\.key === 'Escape'/);
  assert.match(css, /@media\(max-width:760px\)/);
  assert.match(css, /@media\(max-width:390px\)/);
  assert.match(css, /@media\(prefers-reduced-motion:reduce\)/);
  assert.match(css, /#proof-canvas/);
  assert.match(css, /--bg:#efebe3/);
});

test('the sculpture is a self-contained, accessible SVG, not an invented screenshot', () => {
  assert.match(html, /src="\.\/assets\/transformation\.svg"/);
  assert.match(html, /An abstract illustration/);
  assert.match(art, /^<svg /);
  assert.match(art, /<\/svg>\s*$/);
  assert.match(art, /<path /);
});
