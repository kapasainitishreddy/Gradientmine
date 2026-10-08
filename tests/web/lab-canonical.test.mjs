import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {canonicalJson} from '../../web/assets/lab-canonical.mjs';

test('Research Lab client signature bytes match Python sorted compact ASCII JSON', () => {
  assert.equal(canonicalJson({z:1,a:'café',emoji:'🧪'}), '{"a":"caf\\u00e9","emoji":"\\ud83e\\uddea","z":1}');
  assert.equal(canonicalJson({policy_sha256:'a'.repeat(64),format:'gradientmine.lab-submission.v1',
    submitted_at:2000000000,artifact_sha256:'b'.repeat(64),benchmark_id:'sample-id'}),
  '{"artifact_sha256":"'+'b'.repeat(64)+'","benchmark_id":"sample-id","format":"gradientmine.lab-submission.v1","policy_sha256":"'+'a'.repeat(64)+'","submitted_at":2000000000}');
});

test('artifact digests are deterministic regardless of JSON key insertion order', () => {
  const x={format:'gradientmine.safety_policy.v1',allow_terms:[],block_terms:['café']};
  const y={block_terms:['café'],format:'gradientmine.safety_policy.v1',allow_terms:[]};
  assert.equal(
    createHash('sha256').update(canonicalJson(x)).digest('hex'),
    createHash('sha256').update(canonicalJson(y)).digest('hex'),
  );
});

test('signature helper rejects nondeterministic or unsafe numbers', () => {
  assert.throws(() => canonicalJson({a:NaN}), /Non-finite/);
  assert.throws(() => canonicalJson({a:Infinity}), /Non-finite/);
  assert.throws(() => canonicalJson({a:1.5}), /safe integers/);
  assert.throws(() => canonicalJson({a:undefined}), /Unsupported signed JSON/);
});
