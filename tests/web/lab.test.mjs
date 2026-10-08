import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const read = name => readFileSync(new URL(name, import.meta.url), 'utf8');
const html = read('../../web/lab.html');
const client = read('../../web/assets/lab.mjs');
const css = read('../../web/assets/lab.css');
const home = read('../../web/index.html');

test('research lab is discoverable from the preserved GradientMine homepage', () => {
  assert.match(home, /href="\.\/lab\.html">Research Lab/);
  assert.match(html, /Research Lab \| GradientMine/);
  assert.match(html, /Research Lab/);
  assert.match(html, /STATIC SHOWCASE|Checking research service/);
});

test('research UI has no invented live bounties, payments, model claims or unsafe HTML insertion', () => {
  assert.match(html, /zero monetary reward|no rewards, billing or on-chain settlement/i);
  assert.match(html, /held-out|holdout/i);
  assert.doesNotMatch(html, /Total Rewards|\$[0-9][0-9,]*|1000 registered researchers/i);
  assert.doesNotMatch(client, /innerHTML|outerHTML|document\.write\(|\beval\(|new Function\(/);
  assert.match(client, /document\.createElement/);
  assert.match(client, /textContent/);
  assert.match(client, /state\.online=false/);
  assert.match(client, /The research backend is not available/);
});

test('research UI enforces signing and commitment before a candidate is posted', () => {
  assert.match(client, /wallet\.wallet\.features\['solana:signMessage'\]/);
  assert.match(client, /sha256\(encoder\.encode\(stable\(artifact\)\)\)/);
  assert.match(client, /policy_sha256:state\.detail\.policy_sha256/);
  assert.match(client, /verifyEnvelope\(e\.receipt,item\.policy\.validator\)/);
  assert.match(client, /format:'gradientmine\.review\.v1'/);
  assert.match(html, /No funds are transferred/);
});

test('lab responsive and reduced-motion behaviors are present', () => {
  assert.match(css, /@media\(max-width:760px\)/);
  assert.match(css, /@media\(prefers-reduced-motion:reduce\)/);
  assert.match(html, /role="status"/);
  assert.match(html, /aria-live="polite"/);
  assert.match(html, /id="lab-wallet-dialog"/);
  assert.match(html, /id="lab-benchmarks"/);
});
