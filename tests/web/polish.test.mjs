import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const read = file => readFileSync(new URL(file, import.meta.url), 'utf8');
const lab = read('../../web/lab.html');
const site = read('../../web/index.html');
const css = read('../../web/assets/polish.css');
const labCode = read('../../web/assets/lab.mjs');
const motion = read('../../web/assets/editorial.mjs');
const canvas = read('../../web/assets/showcase.mjs');

test('the approved editorial brand remains intact and ships a subtle lighting layer', () => {
  assert.match(site, /DON'T<\/span><span>GUESS\./);
  assert.match(site, /assets\/transformation\.svg/);
  assert.match(site, /stage-light-sweep/);
  assert.match(site, /assets\/polish\.css/);
  assert.match(css, /stage-light-sweep/);
  assert.match(css, /gallery-sweep/);
  assert.match(css, /prefers-reduced-motion: reduce/);
  assert.match(css, /forced-colors: active/);
});

test('native motion only enhances the site and does not change evaluation or payments', () => {
  assert.match(motion, /IntersectionObserver/);
  assert.match(motion, /prefers-reduced-motion: reduce/);
  assert.match(motion, /requestAnimationFrame/);
  assert.match(motion, /aria-expanded/);
  assert.doesNotMatch(motion, /submit|settlement_signature|funding_signature|fake bounty/i);
});

test('the proof canvas pauses work when offscreen or in a hidden tab', () => {
  assert.match(canvas, /visibilitychange/);
  assert.match(canvas, /IntersectionObserver/);
  assert.match(canvas, /cancelAnimationFrame/);
  assert.match(canvas, /!doc.hidden/);
  assert.match(canvas, /render\(performance\.now\(\)\)/);
});

test('lab UI supports accessible workspace access controls and truthful audit labels', () => {
  assert.match(lab, /id="lab-members"/);
  assert.match(lab, /id="lab-audit"/);
  assert.match(lab, /lab-create-disclosure/);
  assert.match(lab, /id="menu-button"/);
  assert.match(lab, /assets\/polish\.css/);
  assert.match(labCode, /refreshWorkspaceSecurity/);
  assert.match(labCode, /MEMBER_REVOKED|Member access revoked/);
  assert.match(labCode, /lab-score-track/);
  assert.match(labCode, /state\.loadedTemplateFor/);
  assert.match(labCode, /from '\.\/lab-canonical\.mjs'/);
  assert.doesNotMatch(labCode, /innerHTML|document\.write\(|\beval\(/);
});

test('hero first paint never depends on an animation hiding content', () => {
  const motionLibrary=read('../../web/assets/motion-layer.mjs');
  assert.match(motionLibrary, /Never hide the main headline or sculpture/);
  assert.doesNotMatch(motionLibrary, /opacity:\[0,1\]/);
  assert.doesNotMatch(motionLibrary, /filter:\['blur/);
  assert.match(motionLibrary, /Native IntersectionObserver in editorial\.mjs/);
});
