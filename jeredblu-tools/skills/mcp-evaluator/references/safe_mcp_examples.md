# Safe MCP Implementation Examples

This reference documents legitimate MCP server patterns that may appear suspicious during security review but are actually safe and expected. Use this to reduce false positives during evaluation.

## Legitimate File System Operations

### Pattern: Scoped File Access
```javascript
// SAFE - Properly restricted file access
const ALLOWED_DIR = path.resolve(__dirname, 'data');

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const filePath = path.join(ALLOWED_DIR, request.params.arguments.filename);

  // Verify path is within allowed directory
  if (!filePath.startsWith(ALLOWED_DIR)) {
    throw new Error('Access denied');
  }

  return fs.readFileSync(filePath, 'utf-8');
});
```
**Why Safe**: Path traversal protection, clear scope limitation.

### Pattern: Temporary File Management
```python
# SAFE - Proper temporary file handling
import tempfile
import os

@server.call_tool()
async def process_file(content: str):
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(content.encode())
        tmp_path = tmp.name

    try:
        result = process(tmp_path)
        return result
    finally:
        os.unlink(tmp_path)  # Clean up
```
**Why Safe**: Uses secure temp files, proper cleanup, limited scope.

## Legitimate External API Calls

### Pattern: Validated External Requests
```javascript
// SAFE - Properly validated external calls
const ALLOWED_APIS = [
  'https://api.github.com',
  'https://api.openai.com'
];

async function makeApiCall(url) {
  const urlObj = new URL(url);
  const baseUrl = `${urlObj.protocol}//${urlObj.host}`;

  if (!ALLOWED_APIS.includes(baseUrl)) {
    throw new Error('Unauthorized API');
  }

  return fetch(url);
}
```
**Why Safe**: Strict allowlist, URL validation, clear boundaries.

### Pattern: Rate-Limited API Access
```python
# SAFE - Responsible API usage with rate limiting
from time import time
from collections import deque

class RateLimiter:
    def __init__(self, max_calls=10, period=60):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()

    def allow(self):
        now = time()
        # Remove old calls
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False

limiter = RateLimiter()

@server.call_tool()
async def api_request(endpoint: str):
    if not limiter.allow():
        raise Exception('Rate limit exceeded')
    return await make_request(endpoint)
```
**Why Safe**: Prevents abuse, protects external services, responsible resource usage.

## Legitimate Credential Management

### Pattern: Environment Variable Credentials
```javascript
// SAFE - Using environment variables for secrets
require('dotenv').config();

const API_KEY = process.env.API_KEY;

if (!API_KEY) {
  throw new Error('API_KEY environment variable required');
}

// Never log or expose
async function authenticate() {
  return fetch('https://api.example.com', {
    headers: { 'Authorization': `Bearer ${API_KEY}` }
  });
}
```
**Why Safe**: Proper secret management, not hardcoded, environment-based.

### Pattern: Encrypted Credential Storage
```python
# SAFE - Encrypted local storage
from cryptography.fernet import Fernet
import keyring

class SecureCredentialStore:
    def __init__(self):
        # Key stored in system keyring
        key = keyring.get_password('mcp-server', 'encryption-key')
        if not key:
            key = Fernet.generate_key()
            keyring.set_password('mcp-server', 'encryption-key', key.decode())
        self.cipher = Fernet(key.encode())

    def store(self, name: str, value: str):
        encrypted = self.cipher.encrypt(value.encode())
        keyring.set_password('mcp-server', name, encrypted.decode())

    def retrieve(self, name: str):
        encrypted = keyring.get_password('mcp-server', name)
        if encrypted:
            return self.cipher.decrypt(encrypted.encode()).decode()
        return None
```
**Why Safe**: Encryption at rest, uses system keyring, proper crypto practices.

## Legitimate Code Execution

### Pattern: Sandboxed Code Execution
```javascript
// SAFE - VM with strict limitations
const vm = require('vm');

function executeSafe(code) {
  const sandbox = {
    console: { log: (...args) => console.log('[SANDBOX]', ...args) },
    // Only safe globals exposed
  };

  const context = vm.createContext(sandbox);
  const script = new vm.Script(code);

  return script.runInContext(context, {
    timeout: 1000,  // 1 second max
    breakOnSigint: true
  });
}
```
**Why Safe**: Isolated context, timeout protection, limited API surface.

### Pattern: Validated Command Execution
```python
# SAFE - Allowlist-based command execution
ALLOWED_COMMANDS = {
    'git_status': ['git', 'status'],
    'git_log': ['git', 'log', '--oneline', '-n', '10']
}

@server.call_tool()
async def run_command(command_name: str):
    if command_name not in ALLOWED_COMMANDS:
        raise ValueError(f'Unknown command: {command_name}')

    cmd = ALLOWED_COMMANDS[command_name]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    return result.stdout
```
**Why Safe**: Strict allowlist, no user input in commands, timeout protection.

## Legitimate Logging & Telemetry

### Pattern: Anonymous Usage Analytics
```javascript
// SAFE - Privacy-respecting analytics
const crypto = require('crypto');

function trackUsage(toolName) {
  // Hash user ID for anonymization
  const userId = process.env.USER;
  const hashedId = crypto.createHash('sha256').update(userId).digest('hex');

  const analytics = {
    tool: toolName,
    user_hash: hashedId,  // Anonymous
    timestamp: new Date().toISOString(),
    version: require('./package.json').version
  };

  // Only if user opted in
  if (process.env.ANALYTICS_ENABLED === 'true') {
    fetch('https://analytics.example.com/track', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(analytics)
    }).catch(() => {}); // Silent fail
  }
}
```
**Why Safe**: Opt-in only, anonymized data, no PII, graceful degradation.

### Pattern: Debug Logging with Sanitization
```python
# SAFE - Sanitized logging
import logging
import re

def sanitize_log(data: dict) -> dict:
    """Remove sensitive fields from logs"""
    sensitive = ['password', 'token', 'api_key', 'secret']
    sanitized = data.copy()

    for key in list(sanitized.keys()):
        if any(s in key.lower() for s in sensitive):
            sanitized[key] = '[REDACTED]'

    return sanitized

@server.call_tool()
async def process_request(args: dict):
    logging.debug(f'Request: {sanitize_log(args)}')
    result = await handle_request(args)
    return result
```
**Why Safe**: Automatic PII redaction, debug-only, follows privacy best practices.

## Legitimate Network Operations

### Pattern: Health Check Endpoints
```javascript
// SAFE - Non-sensitive health monitoring
const express = require('express');
const app = express();

app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    version: require('./package.json').version,
    uptime: process.uptime()
  });
});

app.listen(process.env.HEALTH_PORT || 8080);
```
**Why Safe**: Public info only, standard monitoring pattern, no sensitive data.

### Pattern: Retry Logic with Backoff
```python
# SAFE - Resilient API calls
import asyncio
from typing import Callable

async def retry_with_backoff(
    fn: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0
):
    for attempt in range(max_retries):
        try:
            return await fn()
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            delay = base_delay * (2 ** attempt)
            await asyncio.sleep(delay)
```
**Why Safe**: Error handling best practice, prevents cascading failures, bounded retries.

## Legitimate Data Processing

### Pattern: Input Validation
```javascript
// SAFE - Comprehensive input validation
const validator = require('validator');

function validateInput(args) {
  const errors = [];

  if (!args.email || !validator.isEmail(args.email)) {
    errors.push('Invalid email');
  }

  if (!args.url || !validator.isURL(args.url, { protocols: ['https'] })) {
    errors.push('Invalid URL (HTTPS required)');
  }

  if (!args.count || !Number.isInteger(args.count) || args.count < 1 || args.count > 100) {
    errors.push('Count must be integer between 1-100');
  }

  if (errors.length > 0) {
    throw new Error(`Validation failed: ${errors.join(', ')}`);
  }

  return true;
}
```
**Why Safe**: Strong validation, security best practice, clear boundaries.

### Pattern: Data Caching with TTL
```python
# SAFE - Memory-bounded caching
from datetime import datetime, timedelta
from typing import Any, Optional

class TTLCache:
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self.cache = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            value, expiry = self.cache[key]
            if datetime.now() < expiry:
                return value
            del self.cache[key]
        return None

    def set(self, key: str, value: Any):
        # Evict oldest if at capacity
        if len(self.cache) >= self.max_size:
            oldest = min(self.cache.items(), key=lambda x: x[1][1])
            del self.cache[oldest[0]]

        expiry = datetime.now() + self.ttl
        self.cache[key] = (value, expiry)

cache = TTLCache()
```
**Why Safe**: Bounded memory, automatic expiry, prevents resource exhaustion.

## Legitimate Error Handling

### Pattern: Safe Error Responses
```javascript
// SAFE - Secure error handling
class MCPError extends Error {
  constructor(message, code, isPublic = false) {
    super(message);
    this.code = code;
    this.isPublic = isPublic;
  }
}

server.onerror = (error) => {
  // Log full error internally
  console.error('Internal error:', error);

  // Return sanitized error to client
  if (error instanceof MCPError && error.isPublic) {
    return { error: error.message, code: error.code };
  }

  // Generic error for security
  return { error: 'An error occurred', code: 'INTERNAL_ERROR' };
};
```
**Why Safe**: Prevents information disclosure, proper error handling, security-aware.

## Legitimate Configuration

### Pattern: Type-Safe Configuration
```typescript
// SAFE - Validated configuration with TypeScript
interface Config {
  maxRequestSize: number;
  timeout: number;
  allowedOrigins: string[];
  rateLimitPerHour: number;
}

function loadConfig(): Config {
  const config: Config = {
    maxRequestSize: parseInt(process.env.MAX_REQUEST_SIZE || '1048576'), // 1MB
    timeout: parseInt(process.env.TIMEOUT || '5000'),
    allowedOrigins: (process.env.ALLOWED_ORIGINS || 'localhost').split(','),
    rateLimitPerHour: parseInt(process.env.RATE_LIMIT || '100')
  };

  // Validate bounds
  if (config.maxRequestSize > 10485760) {
    throw new Error('MAX_REQUEST_SIZE too large (max 10MB)');
  }

  if (config.timeout > 30000) {
    throw new Error('TIMEOUT too large (max 30s)');
  }

  return config;
}
```
**Why Safe**: Type safety, validation, reasonable defaults, bounded values.

## Key Differentiators: Safe vs Unsafe

| Safe Pattern | Unsafe Pattern |
|-------------|----------------|
| Environment variables for secrets | Hardcoded credentials |
| Allowlist validation | No validation |
| Scoped file access | Unrestricted paths |
| Rate limiting | Unbounded requests |
| Input sanitization | Direct injection |
| Proper error handling | Error disclosure |
| Opt-in telemetry | Hidden data collection |
| Bounded resources | Resource exhaustion risk |
| Clear documentation | Obfuscated code |
| Sandboxed execution | Direct eval/exec |

## Evaluation Tips

When reviewing MCP code:
1. **Check for safeguards**: Look for validation, limits, sanitization
2. **Verify scope**: Are operations properly bounded?
3. **Review intent**: Is documentation clear about behavior?
4. **Assess proportionality**: Do permissions match stated functionality?
5. **Test edge cases**: What happens with malicious input?

A pattern is likely safe if it:
- Has clear documentation explaining why it's needed
- Includes proper input validation
- Uses industry-standard security libraries
- Has bounded resource usage
- Follows principle of least privilege
- Gracefully handles errors without disclosure

A pattern is likely unsafe if it:
- Lacks validation or sanitization
- Has unbounded resource usage
- Uses deprecated or known-vulnerable dependencies
- Includes obfuscation without source code
- Has hidden or undocumented behaviors
- Violates principle of least privilege
