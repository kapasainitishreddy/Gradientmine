import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {showcaseModel, formatScore} from '../../web/assets/showcase.mjs';

const recorded=JSON.parse(fs.readFileSync(new URL('../../web/assets/recorded-run.json',import.meta.url),'utf8'));

test('cinematic showcase derives only recorded evidence, including unpaid boundary',()=>{
  const model=showcaseModel(recorded.job);
  assert.equal(model.parent, recorded.job.baseline_accuracy);
  assert.equal(model.winner, recorded.job.winner.candidate_accuracy);
  assert.equal(model.delta, recorded.job.winner.delta);
  assert.equal(model.lowerBound, recorded.job.winner.bootstrap_lower_bound);
  assert.equal(model.workers.length,3);
  assert.equal(model.workers.some(x=>x.negativeControl),true);
  assert.equal(model.paid,false);
  assert.equal(model.networkLabel,'LOCAL EVIDENCE');
});

test('showcase does not fabricate a winner before evaluation',()=>{
  const model=showcaseModel({
    mode:'local',state:'OPEN',baseline_accuracy:null,winner:null,
    submissions:[{worker:'abc',worker_metrics:{public_validation_accuracy:.9},state:'REGISTERED'}]
  });
  assert.equal(model.winner,null);
  assert.equal(model.delta,null);
  assert.equal(model.workers[0].assurance,null);
  assert.equal(model.workers[0].status,'SEALED');
  assert.equal(model.paid,false);
});

test('score formatting is concise and honest',()=>{
  assert.equal(formatScore(.9527777777),'95.28');
  assert.equal(formatScore(null),'—');
  assert.equal(formatScore(Number.NaN),'—');
});
