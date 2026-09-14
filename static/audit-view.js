/* Human-readable presentation only; the exported evidence remains unchanged. */
(function (root) {
  'use strict';
  const escape = value => String(value).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
  const words = value => String(value).replace(/_/g, ' ').replace(/\+/g, ' and ');
  const titles = {
    overview: 'List ingredients and quantities', prepare: 'Prepare ingredients',
    blend: 'Blend the pepper mixture', cook_protein: 'Cook the selected protein',
    fry_base: 'Fry the sauce base', reduce_sauce: 'Reduce the tomato sauce',
    season_and_liquid: 'Season and add cooking liquid', add_rice: 'Cook the rice',
    inspect: 'Explain how to check the rice', finish_party: 'Apply the party-style finish',
    finish_regular: 'Apply the regular finish', serve: 'Serve the jollof rice',
    rice_liquid: 'Prepare the cooking liquid', cook_rice: 'Cook the rice',
    inspect_rice: 'Explain how to check the rice', condition_rice: 'Cool and separate the rice',
    fry_onions_protein: 'Fry onions and selected protein', fry_veg: 'Fry the vegetables',
    season: 'Season the fried rice', combine: 'Combine rice and vegetables',
    fry_rice: 'Fry the combined rice', validate: 'Explain the final seasoning and texture checks',
    finish: 'Finish and serve the fried rice'
  };
  const labels = {
    rice_cups: 'Raw rice', rice_type: 'Rice type', spice: 'Spice level',
    protein: 'Protein', style: 'Cooking style', pot_capacity: 'Pot capacity',
    frying_capacity: 'Pan capacity', pot_batches: 'Pot batches', frying_batches: 'Frying batches',
    cooked_cups_raw: 'Unrounded cooked rice estimate', capacity: 'Equipment capacity',
    spring_onions_present: 'Spring onions included'
  };
  const rounding = {
    none: 'No rounding is applied.', count: 'Round to whole items; positive amounts have a minimum of one.',
    half: 'Round to the nearest half; positive amounts have a minimum of one half.',
    quarter: 'Round to the nearest quarter; positive amounts have a minimum of one quarter.',
    grams: 'Round to the nearest 50 grams; positive amounts have a minimum of 50 grams.',
    range: 'Use a practical whole-number amount or a range between adjacent whole numbers.'
  };
  function date(value) {
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? 'Time unavailable' :
      new Intl.DateTimeFormat('en-GB', {dateStyle: 'medium', timeStyle: 'long'}).format(parsed);
  }
  function amount(value, unit = '') {
    return (value === null ? 'To taste' : String(value) + (unit ? ' ' + unit : ''));
  }
  function inputLines(inputs) {
    return Object.entries(inputs).map(([key, value]) => {
      let display = typeof value === 'boolean' ? (value ? 'Yes' : 'No') : words(value);
      if (['rice_cups', 'pot_capacity', 'frying_capacity', 'cooked_cups_raw', 'capacity'].includes(key)) display += ' cups';
      return (labels[key] || words(key)) + ': ' + display;
    });
  }
  function list(value) {
    if (!Array.isArray(value)) return escape(value);
    return '<ul>' + value.map(line => '<li>' + escape(line) + '</li>').join('') + '</ul>';
  }
  function card(fields, technical) {
    return '<div class="audit-record"><dl class="audit-fields">' +
      ['Rule', 'Inputs', 'Explanation', 'Result', 'Execution'].map(key =>
        '<dt>' + key + '</dt><dd>' + list(fields[key]) + '</dd>').join('') +
      '</dl><details class="audit-technical"><summary>Technical details</summary><pre>' +
      escape(JSON.stringify(technical, null, 2)) + '</pre></details></div>';
  }
  function ruleTitle(id) {
    const name = id.split('.').pop();
    return titles[name] || words(name).replace(/^./, c => c.toUpperCase());
  }
  function conditionLines(conditions, plan) {
    const flags = {
      ready: 'Recipe inputs and quantity calculations must be ready.',
      protein_present: 'A protein must be selected.', protein_none: 'No protein must be selected.',
      style_party: 'Party style must be selected.', style_regular: 'Regular style must be selected.'
    };
    return conditions.map(c => {
      let reason;
      if (c.fact_type === 'Flag' && c.kind === 'present') reason = flags[c.fields.name];
      if (c.fact_type === 'Step' && c.kind === 'absent') {
        const step = plan.steps.find(s => s.order === c.fields.order);
        reason = 'The ' + (step ? step.phase.toLowerCase() : 'output') + ' step must not already exist.';
      }
      return (c.satisfied ? 'Met: ' : 'Not met: ') + (reason || 'Additional condition; see technical details.');
    });
  }
  function decisionLine(d) {
    if (d.expression === 'protein == none') return d.result ? 'No protein was selected; use the vegetarian instructions.' : 'A protein was selected; use the protein instructions.';
    if (d.expression === 'protein != none') return d.result ? 'A protein was selected; include it in this step.' : 'No protein was selected; leave it out of this step.';
    if (['pot_batches > 1', 'frying_batches > 1'].includes(d.expression)) {
      const count = d.inputs.pot_batches ?? d.inputs.frying_batches;
      return d.result ? 'The quantity needs ' + count + ' batches; include the instruction to divide it.' : 'The quantity fits in one batch; no division is needed.';
    }
    if (d.expression === 'spring_onions in ingredients') return d.result ? 'Spring onions are included; add the optional finishing instruction.' : 'Spring onions are absent; omit the optional finishing instruction.';
    return 'An additional decision was evaluated; see technical details.';
  }
  function calculation(ing) {
    const d = ing.derivation;
    const inputs = ['Rice: ' + amount(d.rice_cups ?? d.raw_amount, 'cups')];
    if (d.ratio != null) inputs.push('Ratio: ' + amount(d.ratio, ing.unit) + ' per cup of rice');
    let explanation;
    if (d.formula === 'User input') explanation = ['Use the rice quantity you entered.'];
    else if (d.raw_amount === null) explanation = ['This ingredient is added to taste; no fixed quantity is calculated.'];
    else if (d.formula === 'protein == none → 0') explanation = ['No protein was selected, so the quantity is zero.'];
    else explanation = [d.rice_cups + ' × ' + d.ratio + ' = ' + amount(d.raw_amount, ing.unit),
      rounding[d.rounding] || 'See technical details for the display policy.',
      ...(d.raw_amount === 0 ? ['Zero stays zero; no minimum amount is added.'] : [])];
    return '<details><summary>How much and why?</summary>' + card({
      Rule: (ing.key === 'rice' ? 'Set ' : 'Calculate ') + ing.label.toLowerCase(),
      Inputs: inputs, Explanation: explanation,
      Result: d.raw_amount === null ? 'To taste' :
        'Calculated: ' + amount(d.raw_amount, ing.unit) + ' → Use: ' + amount(ing.amount, ing.unit),
      Execution: 'Quantity calculation, before the cooking rules run.'
    }, {source: d.source, derivation: d}) + '</details>';
  }
  function firing(event, plan) {
    if (!event) return '';
    const inputs = inputLines(plan.params);
    event.decisions.forEach(d => inputs.push(...inputLines(d.inputs)));
    return card({
      Rule: ruleTitle(event.rule_id), Inputs: [...new Set(inputs)],
      Explanation: [...conditionLines(event.conditions, plan), ...event.decisions.map(decisionLine)],
      Result: event.outputs.map(output => {
        const index = plan.steps.findIndex(step => step.order === output.order);
        return 'Added ' + (index >= 0 ? 'step ' + (index + 1) + ': ' : '') + output.phase + '.';
      }),
      Execution: 'Fired #' + event.sequence + ' · ' + date(event.fired_at) + '. This is when the instruction was generated.'
    }, event);
  }
  function skipped(event, plan) {
    return card({
      Rule: ruleTitle(event.rule_id), Inputs: inputLines(plan.params),
      Explanation: conditionLines(event.conditions, plan), Result: 'No cooking step was added by this rule.',
      Execution: 'Did not fire. Conditions shown here were checked at the end of the run.'
    }, event);
  }
  function overview(plan) {
    const a = plan.audit;
    const derived = a.derived;
    const result = [plan.ingredients.length + ' ingredient quantities and ' + plan.steps.length + ' cooking steps.'];
    if (derived.pot_batches) result.push('Pot batches: ' + derived.pot_batches);
    if (derived.frying_batches) result.push('Frying batches: ' + derived.frying_batches);
    return card({
      Rule: 'Generate the ' + plan.dish + ' guide', Inputs: inputLines(plan.params),
      Explanation: 'Use one validated recipe configuration for all quantities and cooking rules.',
      Result: result, Execution: date(a.generated_at) + ' · ' + a.firings.length + ' cooking rules fired.'
    }, {run_id: a.run_id, config_hash: a.config_hash, implementation_hash: a.implementation_hash,
      runtime: a.runtime, initial_facts: a.initial_facts, derived: a.derived});
  }
  root.AuditView = {calculation, firing, skipped, overview, date};
})(typeof module === 'object' && module.exports ? module.exports : globalThis);
