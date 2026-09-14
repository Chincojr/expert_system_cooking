const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {AuditView} = require('./static/audit-view.js');
const sample = name => JSON.parse(fs.readFileSync(`docs/evidence/${name}.json`, 'utf8'));
const visible = html => html.split('<details class="audit-technical">')[0];

test('quantity and firing explanations share readable fields without raw identifiers', () => {
  const plan = sample('jollof_party');
  const ingredient = plan.ingredients.find(i => i.key === 'bay_leaves');
  const firing = plan.audit.firings.find(f => f.rule_id.endsWith('.prepare'));
  const quantity = AuditView.calculation(ingredient);
  const step = AuditView.firing(firing, plan);
  for (const html of [quantity, step, AuditView.overview(plan)]) {
    for (const label of ['Rule', 'Inputs', 'Explanation', 'Result', 'Execution']) assert.ok(html.includes(`<dt>${label}</dt>`));
    assert.ok(!visible(html).includes('JollofRiceEngine'));
    assert.ok(!visible(html).includes('fact_ids'));
    assert.ok(!visible(html).includes('&quot;name&quot;'));
    assert.ok(html.includes('<summary>Technical details</summary>'));
  }
  assert.ok(visible(quantity).includes('3 × 0.67 = 2.01'));
  assert.ok(visible(quantity).includes('Round to whole items'));
  assert.ok(visible(step).includes('Prepare ingredients'));
  assert.ok(visible(step).includes('Met: Recipe inputs and quantity calculations must be ready.'));
  assert.ok(!visible(step).includes('\u2014'));
  assert.ok(visible(step).includes('Added step 2: Prepare.'));
  assert.ok(!visible(step).includes(firing.fired_at));
  assert.ok(step.includes(firing.rule_id)); // Still retained in the collapsed evidence.
});

test('skipped rules and batching use their actual evidence', () => {
  const veggie = sample('jollof_vegetarian');
  const skipped = veggie.audit.not_fired.find(f => f.rule_id.endsWith('.cook_protein'));
  const text = visible(AuditView.skipped(skipped, veggie));
  assert.ok(text.includes('Not met: A protein must be selected.'));
  assert.ok(!text.includes('\u2014'));
  assert.ok(text.includes('Did not fire'));
  assert.ok(text.includes('end of the run'));
  const fried = sample('fried_rice_boundary');
  const combine = fried.audit.firings.find(f => f.rule_id.endsWith('.combine'));
  const batching = visible(AuditView.firing(combine, fried));
  assert.ok(batching.includes('needs 2 batches'));
  assert.ok(batching.includes('6.03 cups'));
  const oneBatch = structuredClone(combine);
  oneBatch.decisions[0].result = false;
  oneBatch.decisions[0].inputs.frying_batches = 1;
  assert.ok(visible(AuditView.firing(oneBatch, fried)).includes('fits in one batch'));
});

test('rice input, absent protein and to-taste quantities remain distinct', () => {
  const plan = sample('jollof_vegetarian');
  const html = key => visible(AuditView.calculation(plan.ingredients.find(i => i.key === key)));
  assert.ok(html('rice').includes('Use the rice quantity you entered.'));
  assert.ok(html('protein').includes('No protein was selected, so the quantity is zero.'));
  assert.ok(html('salt').includes('no fixed quantity is calculated'));
});

test('user and configuration text is escaped in summaries and technical details', () => {
  const plan = sample('jollof_party');
  plan.params.protein = '<img src=x onerror=alert(1)>';
  plan.ingredients[1].label = '<script>alert(1)</script>';
  for (const html of [AuditView.firing(plan.audit.firings[0], plan), AuditView.calculation(plan.ingredients[1])]) {
    assert.ok(!html.includes('<script>'));
    assert.ok(!html.includes('<img'));
    assert.ok(html.includes('&lt;'));
  }
});

test('page loads the presenter before its inline script and JavaScript parses', () => {
  const html = fs.readFileSync('static/index.html', 'utf8');
  assert.ok(html.indexOf('src="/static/audit-view.js"') < html.indexOf('<script>'));
  new vm.Script(html.match(/<script>([\s\S]*?)<\/script>/)[1]);
});
