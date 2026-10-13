# MCP safeguards: evidence, not automatic passes

Use these counterexamples to avoid both false positives and false assurances. Snippets are review prompts, not reusable security implementations. Do not run target-server code to test them during a static review.

## Paths

`candidate.startsWith(allowedDir)` is **not containment**: `/data/private-other` begins with `/data/private`. Normalizing separators does not handle symlink escapes or races. Trace path canonicalization, component-aware containment, symlinks, file-open timing, and filesystem ownership. A scoped read can be legitimate; a declared directory is not proof that reads stay there.

## Network requests

An exact URL-origin allowlist can constrain initial destinations but default redirect following can reach a disallowed host. Check redirects, credentials in URLs, DNS/IP handling and private network exposure where attacker-controlled destinations are relevant. A generic HTTPS/URL validator is not an SSRF defense. Documented external API calls are expected functionality, not inherently exfiltration; inspect actual transmitted fields and credentials.

## Execution

Node `vm` provides JavaScript contexts, **not a security sandbox for untrusted code**. A timeout or a small globals object does not prove isolation. Require a real isolation boundary appropriate to the deployment, or report the exposure. General-purpose execution may be intentional, but the user's authority and client approval cannot be silently expanded.

Fixed subprocess argument arrays avoid shell interpolation, but selected programs can read configuration, spawn pagers or load hooks/helpers. Review working directory, environment, repository ownership, configuration and subprocess capabilities. Never mark all `subprocess` or `exec` use malicious based on spelling alone.

## Credentials and logs

Environment variables avoid embedding secrets in source; they do not prove safe storage, scopes, logging or forwarding. Plaintext local storage is not automatically critical: consider file permissions, local threat model and sensitivity. Encryption with a colocated broadly readable key is not a complete boundary.

Deleting top-level keys named `password` or `token` does not sanitize nested objects, free text, headers or unexpected names. Debug logging and server-side error logs can still expose secrets even if user-visible messages are generic. Inspect real paths and field shapes.

## Telemetry

Hashing a username is not anonymization: low-entropy usernames can be guessed and stable hashes remain linkable. Opt-in controls help only if defaults, payloads and all send paths honor them. Prefer minimization; don't label data anonymous merely because hashing is present.

## Limits and configuration

TypeScript types are not runtime validation. `parseInt` can produce NaN or accept prefixes; checking only `value > maximum` accepts NaN, zero and negatives. Check finite/integer/lower/upper bounds where relevant. A TTL cache or in-memory rate limiter may have concurrency/per-client/restart gaps; assess deployment context instead of asserting complete protection.

## Transport context

A locally launched stdio server need not implement HTTP authentication. Review its owner, inherited environment, process privileges and who can control inputs/launch configuration instead. For HTTP, inspect actual bind address, authentication/authorization, session boundaries, browser-origin handling and transport protection. Local HTTP is not identical to stdio; loopback alone does not resolve browser-origin risks. A public health endpoint is not automatically a data leak; inspect exposed fields. Tool `readOnlyHint` or `destructiveHint` annotations and a client's confirmation UI are not enforced server permissions.
