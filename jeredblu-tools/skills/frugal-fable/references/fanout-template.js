export const meta = {
  name: 'frugal-fable-fanout',
  description: 'Frugal Fable fan-out template: route independent slices to the cheapest sufficient model, verify, synthesize. COPY AND ADAPT per task — do not run blind.',
  phases: [
    { title: 'Work', detail: 'one agent per slice, model chosen by slice.tier, writes to scratch file' },
    { title: 'Verify', detail: 'Sonnet adversarial pass on high-stakes slices only' },
    { title: 'Synthesize', detail: 'Fable (session model) integrates from files on demand' },
  ],
}

// ── How to use ──────────────────────────────────────────────────────────────
// Pass `args` as an array of slice specs. Fable (the orchestrator) fills these
// in after decomposing the task — that decomposition is the part worth Fable's
// tokens; this script just executes the fan-out cheaply.
//
//   args = [
//     { id: 'scan-auth',  tier: 'haiku',  highStakes: false,
//       prompt: 'Inventory every call site of `authToken` ...',
//       scratch: '.frugal-fable/scan-auth/findings.md' },
//     { id: 'patch-login', tier: 'sonnet', highStakes: true,
//       prompt: 'Apply this bounded change to src/login.ts ... run `npm test -- login`.',
//       scratch: '.frugal-fable/patch-login/report.md' },
//     ...
//   ]
//
// Each slice's `tier` comes from the routing table (haiku | sonnet | opus).
// Score stakes/reversibility/ambiguity → highest sets the floor. When unsure,
// go up one tier. Keep architectural/one-way slices OUT of this fan-out — Fable
// owns those directly.
// ─────────────────────────────────────────────────────────────────────────────

const slices = Array.isArray(args) ? args : []
if (slices.length === 0) {
  return { error: 'No slices passed. args must be an array of { id, tier, highStakes, prompt, scratch }.' }
}

const RESULT_SCHEMA = {
  type: 'object',
  required: ['path', 'summary', 'confidence'],
  properties: {
    path: { type: 'string', description: 'scratch file the agent wrote (NOT the full content)' },
    summary: { type: 'string', description: '<=3 lines: what was done / found' },
    confidence: { enum: ['high', 'medium', 'low'] },
    verifyPassed: { type: 'boolean', description: 'did the required build/tests pass?' },
    stoppedShort: { type: 'boolean', description: 'true if a stop condition was hit' },
  },
}
const VERDICT_SCHEMA = {
  type: 'object',
  required: ['sound', 'evidence'],
  properties: {
    sound: { type: 'boolean' },
    evidence: { type: 'string' },
    confidence: { enum: ['high', 'medium', 'low'] },
  },
}

const tierToModel = t => (t === 'opus' ? 'opus' : t === 'sonnet' ? 'sonnet' : 'haiku')

const workPrompt = s =>
  '## Frugal Fable worker: ' + s.id + '\n\n' +
  s.prompt + '\n\n' +
  '## Output protocol (MANDATORY)\n' +
  '1. Write your full findings / patch / logs to: `' + s.scratch + '` (create dirs as needed).\n' +
  '2. Return ONLY: the path, a <=3-line summary, and your confidence. Do NOT paste the full content back.\n' +
  '3. If your slice requires a build/test, run it and set verifyPassed accordingly.\n' +
  '4. Stop conditions: if the code does not match this prompt, a command fails after one retry, or you need\n' +
  '   out-of-scope files — stop, set stoppedShort=true, and report what blocked you. Do not improvise.\n\n' +
  'Structured output only.'

// ── Work + verify, pipelined (no barrier): each slice verifies as soon as it's done ──
phase('Work')
const done = await pipeline(
  slices,

  s => agent(workPrompt(s), {
    label: 'work:' + s.id,
    phase: 'Work',
    model: tierToModel(s.tier),
    schema: RESULT_SCHEMA,
  }).then(r => (r ? { ...s, result: r } : null)),

  item => {
    if (!item) return null
    // Only high-stakes slices pay for an adversarial verify pass.
    if (!item.highStakes) return item
    return agent(
      '## Adversarial verifier for slice: ' + item.id + '\n\n' +
      'A worker reported: "' + item.result.summary + '" (confidence ' + item.result.confidence + ').\n' +
      'Its output is at `' + item.result.path + '`. Read it.\n\n' +
      'Be skeptical. Does the file actually accomplish the slice objective below, with evidence?\n' +
      'Check the diff/claims against the stated scope. If it touched out-of-scope files, overreached,\n' +
      'or its tests do not actually cover the change, set sound=false.\n\n' +
      '## Slice objective\n' + item.prompt + '\n\nStructured output only.',
      { label: 'verify:' + item.id, phase: 'Verify', model: 'sonnet', schema: VERDICT_SCHEMA }
    ).then(v => ({ ...item, verdict: v }))
  }
)

const results = done.filter(Boolean)
const flagged = results.filter(r => r.verdict && !r.verdict.sound)
const stopped = results.filter(r => r.result.stoppedShort)
log(results.length + ' slices done · ' + flagged.length + ' flagged by verify · ' + stopped.length + ' stopped short')

// ── Synthesize: inherits the session model (Fable). This is the call worth full quality. ──
// Fable reads the scratch files ON DEMAND — the manifest below carries only paths+summaries,
// keeping the context firewall intact. Pull a file in only when integrating it.
phase('Synthesize')
const manifest = results.map(r =>
  '- [' + r.id + '] tier=' + r.tier +
  ' · confidence=' + r.result.confidence +
  (r.verdict ? ' · verify=' + (r.verdict.sound ? 'sound' : 'FLAGGED: ' + r.verdict.evidence) : '') +
  (r.result.stoppedShort ? ' · STOPPED SHORT' : '') +
  '\n  file: ' + r.result.path +
  '\n  summary: ' + r.result.summary
).join('\n')

return {
  task: 'frugal-fable fan-out',
  sliceCount: slices.length,
  completed: results.length,
  flagged: flagged.map(r => ({ id: r.id, why: r.verdict.evidence, file: r.result.path })),
  stoppedShort: stopped.map(r => ({ id: r.id, file: r.result.path })),
  manifest,
  next: 'Fable: read flagged + high-stakes files from the manifest, integrate, run final review. ' +
        'Do NOT trust summaries for high-impact decisions — reopen the file.',
}
