# Security Lens

## When to Equip

Use when reviewing authentication, authorization, input handling, cryptography,
session management, or any code that processes user data or external systems.

## Focus Areas

- [ ] Input validation and sanitization on all external inputs
- [ ] Authentication checks present and correctly enforced
- [ ] Authorization checks - proper role/permission verification before actions
- [ ] SQL injection protection - parameterized queries, no string concatenation
- [ ] XSS protection - output encoding, CSP headers, sanitized rendering
- [ ] CSRF protection - tokens present and validated on state-changing operations
- [ ] Secrets management - no hardcoded keys, tokens, passwords
- [ ] Cryptography - strong algorithms, proper key management, no custom crypto
- [ ] Session management - secure cookies, proper expiration, invalidation on logout
- [ ] Error handling - no stack traces leaked to users
- [ ] Dependency security - no known vulnerable dependencies
- [ ] Rate limiting - protection against brute force and abuse
- [ ] Logging - sensitive data not logged, security events are logged

## Patterns to Flag

- Hardcoded secrets, API keys, or credentials in source code
- Raw SQL string concatenation with user input
- `dangerouslySetInnerHTML` without sanitization
- Missing `HttpOnly`, `Secure`, or `SameSite` on cookies
- Broad CORS origins (`*`) on authenticated endpoints
- `eval()`, `exec()`, `subprocess.call(shell=True)` with user-controlled input
- Missing authentication middleware on protected routes
- JWT tokens without expiration or with weak signing algorithms
- Password storage without bcrypt/scrypt/argon2
- Unvalidated redirects and forwards

## Reference

- OWASP Top 10 (2021)
- OWASP ASVS
- CWE Top 25
