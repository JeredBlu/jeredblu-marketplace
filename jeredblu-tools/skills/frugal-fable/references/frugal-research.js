export const meta = {
  name: 'frugal-research',
  description: 'Hard-budget-capped deep research. Same Haiku-collect → Sonnet-verify → synthesize shape as deep-research-cheap, but with absolute caps (4 angles / 8 fetches / 10 claims / 2 votes) and a token-budget gate that STOPS fanning out before it can blow your usage. Synthesis pinned to Sonnet so it never silently spends premium tokens. Use when you must not exceed a usage limit.',
  whenToUse: 'When you want deep research but on a hard token budget — e.g. constrained usage window, or running under no supervision. Pass the question as args (a string), or { question, capTokens } where capTokens is a TOTAL-token budget (default 1.2M; a focused run lands ~0.9-1M). Pass args as a real JSON object, not a stringified one.',
  phases: [
    { title: 'Scope', detail: 'decompose into <=4 angles' },
    { title: 'Search', detail: 'Haiku, one per angle, bdata + WebSearch' },
    { title: 'Fetch', detail: 'Haiku, <=8 sources, extract claims to context only as summaries' },
    { title: 'Verify', detail: 'Sonnet, <=10 claims x 2 votes, budget-gated' },
    { title: 'Synthesize', detail: 'Sonnet (pinned) — cheap, never Fable' },
  ],
}

// ─── HARD CAPS — the PRIMARY brake. These bound how many pages get read, which is the real
// cost driver (input tokens). Do not raise them to "be thorough"; that's what blew usage. ───
const MAX_ANGLES = 4
const MAX_FETCH = 8
const MAX_VERIFY_CLAIMS = 10
const VOTES_PER_CLAIM = 2
const REFUTATIONS_REQUIRED = 2          // both voters must refute to kill (lenient survival, cheap)

// ─── Budget gate — the SECONDARY brake, and a subtle one. ───
// budget.spent() counts OUTPUT tokens only. Empirically, TOTAL tokens (the thing your usage
// limit actually meters) run ~8-12x output, because reading web pages is input-heavy. So we
// treat capTokens as a TOTAL budget and convert to an output ceiling via IO_RATIO. A run that
// reports ~85k output ≈ ~900k total. Default 1.2M total ≈ ~120k output.
const DEFAULT_CAP_TOTAL = 1_200_000
const IO_RATIO = 10                     // total ≈ IO_RATIO * output (observed); override via args.ioRatio
const RESERVE_FRAC = 0.1                // keep 10% of the output ceiling in reserve for synthesis

// args may be: a bare question string, a JSON string of {question,...}, or a real object.
let A = args
if (typeof args === 'string') {
  const s = args.trim()
  A = s.startsWith('{') ? (() => { try { return JSON.parse(s) } catch { return { question: s } } })() : { question: s }
}
const Q = (A && typeof A.question === 'string' ? A.question : '').trim()
if (!Q) return { error: 'No question. Pass args as a question string or { question, capTokens? }.' }
const capTotal = (A && Number(A.capTokens)) || DEFAULT_CAP_TOTAL
const ioRatio = (A && Number(A.ioRatio)) || IO_RATIO

// Output ceiling = capTotal/ioRatio, also never exceeding any +Nk output target the user set.
const outCeiling = budget.total ? Math.min(capTotal / ioRatio, budget.total) : capTotal / ioRatio
const reserve = outCeiling * RESERVE_FRAC
const headroom = () => outCeiling - budget.spent()
const canAfford = (perAgentOut) => headroom() - reserve > perAgentOut
log('Budget: ~' + Math.round(capTotal / 1000) + 'k total token cap (≈' + Math.round(outCeiling / 1000) + 'k output, ' + ioRatio + 'x assumed)')

const SCOPE_SCHEMA = { type: 'object', required: ['angles'], properties: {
  angles: { type: 'array', minItems: 2, maxItems: MAX_ANGLES, items: {
    type: 'object', required: ['label', 'query'],
    properties: { label: { type: 'string' }, query: { type: 'string' }, rationale: { type: 'string' } } } } } }
const SEARCH_SCHEMA = { type: 'object', required: ['results'], properties: {
  results: { type: 'array', maxItems: 5, items: {
    type: 'object', required: ['url', 'title', 'relevance'],
    properties: { url: { type: 'string' }, title: { type: 'string' }, snippet: { type: 'string' },
      relevance: { enum: ['high', 'medium', 'low'] } } } } } }
const EXTRACT_SCHEMA = { type: 'object', required: ['claims', 'sourceQuality'], properties: {
  sourceQuality: { enum: ['primary', 'secondary', 'blog', 'forum', 'unreliable'] },
  scratchFile: { type: 'string' },
  claims: { type: 'array', maxItems: 4, items: {
    type: 'object', required: ['claim', 'quote', 'importance'],
    properties: { claim: { type: 'string' }, quote: { type: 'string' },
      importance: { enum: ['central', 'supporting', 'tangential'] } } } } } }
const VERDICT_SCHEMA = { type: 'object', required: ['refuted', 'evidence'], properties: {
  refuted: { type: 'boolean' }, evidence: { type: 'string' }, confidence: { enum: ['high', 'medium', 'low'] } } }
const REPORT_SCHEMA = { type: 'object', required: ['summary', 'findings', 'caveats'], properties: {
  summary: { type: 'string' },
  findings: { type: 'array', items: { type: 'object', required: ['claim', 'confidence', 'sources'],
    properties: { claim: { type: 'string' }, confidence: { enum: ['high', 'medium', 'low'] },
      sources: { type: 'array', items: { type: 'string' } }, evidence: { type: 'string' } } } },
  caveats: { type: 'string' }, openQuestions: { type: 'array', items: { type: 'string' } } } }

const slug = Q.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 40).replace(/-+$/, '')
const SCRATCH = './.frugal-fable/' + (slug || 'research')

// ─── Scope ───
phase('Scope')
const scope = await agent(
  'Decompose this research question into at most ' + MAX_ANGLES + ' complementary web-search angles. ' +
  'Be economical — pick the angles with the highest signal, do not pad to the max.\n\n## Question\n' + Q +
  '\n\nReturn the angles. Structured output only.',
  { label: 'scope', schema: SCOPE_SCHEMA, model: 'haiku' }
)
if (!scope) return { error: 'Scope failed.' }
const angles = scope.angles.slice(0, MAX_ANGLES)
log('Angles: ' + angles.map(a => a.label).join(', '))

// ─── dedup + fetch-slot state ───
const normURL = u => { try { const p = new URL(u); return (p.hostname.replace(/^www\./, '') + p.pathname.replace(/\/$/, '')).toLowerCase() } catch { return u.toLowerCase() } }
const seen = new Set()
const relRank = { high: 0, medium: 1, low: 2 }
let fetchSlots = MAX_FETCH

const SEARCH_PROMPT = a =>
  '## Web searcher: ' + a.label + '\nQuestion: "' + Q + '"\nAngle: ' + (a.rationale || '') + '\nQuery: `' + a.query + '`\n\n' +
  'Run WebSearch. If `bdata` is available, ALSO `bdata search "<query>" --json` via Bash (skip silently if missing). ' +
  'Merge, return the top 3-5 results most relevant to the ORIGINAL question. Skip SEO spam. Structured output only.'

const FETCH_PROMPT = (s, ang) =>
  '## Source extractor\nQuestion: "' + Q + '"\nURL: ' + s.url + '\nTitle: ' + s.title + '\nVia: ' + ang + '\n\n' +
  '1. WebFetch the page (fall back to `bdata scrape "<url>" --format markdown` via Bash on block/paywall; skip silently if missing).\n' +
  '2. Write the full extracted notes to a file under `' + SCRATCH + '/` — that path is RELATIVE TO THE CURRENT WORKING DIRECTORY (the repo root); do not write under $HOME. mkdir -p it first. Return the path as scratchFile (CONTEXT FIREWALL — do not paste the full page back).\n' +
  '3. Return 2-4 FALSIFIABLE claims (each with a direct quote + central/supporting/tangential) and the source quality.\n' +
  'If both fetch methods fail or the page is irrelevant, return claims: [] and sourceQuality: "unreliable". Structured output only.'

const VERIFY_PROMPT = (c, v) =>
  '## Adversarial verifier (voter ' + (v + 1) + '/' + VOTES_PER_CLAIM + ')\nBe skeptical — try to REFUTE.\n\n' +
  'Question: ' + Q + '\nClaim: "' + c.claim + '"\nSource: ' + c.sourceUrl + ' (' + c.sourceQuality + ')\nQuote: "' + c.quote + '"\n\n' +
  'WebSearch (or bdata) for contradicting evidence. refuted=true if unsupported by the quote / contradicted / ' +
  'low-quality source for a strong claim / outdated / marketing. Default to refuted=true if uncertain. Structured output only.'

// ─── Search → dedup → fetch (pipelined, budget-gated) ───
phase('Search')
const fetched = await pipeline(
  angles,
  a => {
    if (!canAfford(6_000)) { log('budget gate: skipping search ' + a.label); return null }
    return agent(SEARCH_PROMPT(a), { label: 'search:' + a.label, phase: 'Search', schema: SEARCH_SCHEMA, model: 'haiku' })
      .then(r => r ? { angle: a.label, results: r.results } : null)
  },
  sr => {
    if (!sr) return null
    const novel = [...sr.results].sort((x, y) => relRank[x.relevance] - relRank[y.relevance]).filter(r => {
      const k = normURL(r.url)
      if (seen.has(k) || fetchSlots <= 0) return false
      seen.add(k); fetchSlots--; return true
    })
    return parallel(novel.map(s => () => {
      if (!canAfford(8_000)) { log('budget gate: skipping fetch ' + s.url); return null }
      let host = 'src'; try { host = new URL(s.url).hostname.replace(/^www\./, '') } catch {}
      return agent(FETCH_PROMPT(s, sr.angle), { label: 'fetch:' + host, phase: 'Fetch', schema: EXTRACT_SCHEMA, model: 'haiku' })
        .then(e => e ? { url: s.url, angle: sr.angle, sourceQuality: e.sourceQuality, scratchFile: e.scratchFile,
          claims: e.claims.map(c => ({ ...c, sourceUrl: s.url, sourceQuality: e.sourceQuality })) } : null)
        .catch(() => null)
    }))
  }
)

const sources = fetched.flat().filter(Boolean)
const impRank = { central: 0, supporting: 1, tangential: 2 }
const qualRank = { primary: 0, secondary: 1, blog: 2, forum: 3, unreliable: 4 }
const claims = sources.flatMap(s => s.claims)
  .sort((a, b) => (impRank[a.importance] - impRank[b.importance]) || (qualRank[a.sourceQuality] - qualRank[b.sourceQuality]))
  .slice(0, MAX_VERIFY_CLAIMS)
log('Fetched ' + sources.length + ' sources → verifying top ' + claims.length + ' claims · spent so far ' + Math.round(budget.spent() / 1000) + 'k')

// ─── Verify (budget-gated per claim) ───
phase('Verify')
const voted = (await parallel(claims.map(c => () => {
  if (!canAfford(VOTES_PER_CLAIM * 5_000)) { log('budget gate: skipping verify of "' + c.claim.slice(0, 40) + '"'); return null }
  return parallel(Array.from({ length: VOTES_PER_CLAIM }, (_, v) => () =>
    agent(VERIFY_PROMPT(c, v), { label: 'v' + v, phase: 'Verify', schema: VERDICT_SCHEMA, model: 'sonnet' })
  )).then(vs => {
    const valid = vs.filter(Boolean)
    const refuted = valid.filter(x => x.refuted).length
    const survives = valid.length >= REFUTATIONS_REQUIRED && refuted < REFUTATIONS_REQUIRED
    log('"' + c.claim.slice(0, 45) + '": ' + (valid.length - refuted) + '-' + refuted + (survives ? ' ✓' : ' ✗'))
    return { ...c, refutedVotes: refuted, survives }
  })
}))).filter(Boolean)

const confirmed = voted.filter(c => c.survives)
const killed = voted.filter(c => !c.survives)
log('Verified ' + voted.length + ' → ' + confirmed.length + ' confirmed, ' + killed.length + ' killed')

// ─── Synthesize — PINNED to Sonnet (never inherits Fable; that's the cost guarantee) ───
phase('Synthesize')
const block = confirmed.map((c, i) => '### [' + i + '] ' + c.claim + '\nVote ' + (VOTES_PER_CLAIM - c.refutedVotes) + '-' + c.refutedVotes +
  ' · ' + c.sourceUrl + ' (' + c.sourceQuality + ')\nQuote: "' + c.quote + '"').join('\n\n')

const report = confirmed.length === 0 ? null : await agent(
  '## Synthesis\nQuestion: ' + Q + '\n\n' + confirmed.length + ' claims survived ' + VOTES_PER_CLAIM +
  '-vote verification. Merge duplicates, group into findings that answer the question, assign confidence, ' +
  'write a 3-5 sentence summary, list caveats + open questions.\n\n## Confirmed\n' + block + '\n\nStructured output only.',
  { label: 'synthesize', schema: REPORT_SCHEMA, model: 'sonnet' }
)

return {
  question: Q,
  ...(report || { summary: confirmed.length ? 'Synthesis skipped.' : 'No claims survived verification.', findings: [], caveats: '' }),
  scratchDir: SCRATCH,
  refuted: killed.map(c => ({ claim: c.claim, source: c.sourceUrl })),
  sources: sources.map(s => ({ url: s.url, quality: s.sourceQuality, file: s.scratchFile })),
  stats: {
    angles: angles.length, sources: sources.length, claimsVerified: voted.length,
    confirmed: confirmed.length, killed: killed.length,
    outputTokensSpent: budget.spent(),
    estimatedTotalTokens: budget.spent() * ioRatio,   // the figure that maps to your usage meter
    capTotalTokens: capTotal, outputCeiling: Math.round(outCeiling),
    hitBudgetGate: headroom() <= reserve,
  },
}
