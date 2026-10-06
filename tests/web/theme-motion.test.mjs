import test from 'node:test';
import assert from 'node:assert/strict';
import {THEMES, THEME_ORDER, normalizeTheme, nextTheme, themeMetaColor} from '../../web/assets/theme.mjs';
import {MOTION_CDN, motionAllowed} from '../../web/assets/motion-layer.mjs';

test('theme registry is stable and contains three distinct judge-ready themes', () => {
  assert.deepEqual(THEME_ORDER, ['void', 'aurora', 'paper']);
  assert.equal(Object.keys(THEMES).length, 3);
  assert.equal(new Set(Object.values(THEMES).map(x => x.label)).size, 3);
  for (const name of THEME_ORDER) assert.match(themeMetaColor(name), /^#[0-9a-f]{6}$/i);
});

test('theme normalization and cycling never accepts arbitrary DOM attributes', () => {
  assert.equal(normalizeTheme('aurora'), 'aurora');
  assert.equal(normalizeTheme('javascript:alert(1)'), 'void');
  assert.equal(nextTheme('void'), 'aurora');
  assert.equal(nextTheme('aurora'), 'paper');
  assert.equal(nextTheme('paper'), 'void');
  assert.equal(nextTheme('unknown'), 'aurora');
});

test('Motion runtime is pinned and reduced-motion can disable enhancement', () => {
  assert.equal(MOTION_CDN, 'https://cdn.jsdelivr.net/npm/motion@13.5.0/+esm');
  assert.equal(motionAllowed({matches:false}), true);
  assert.equal(motionAllowed({matches:true}), false);
  assert.equal(motionAllowed(null), true);
});
