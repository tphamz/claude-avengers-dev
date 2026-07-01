# Go Toolbelt

## When to Equip

Use when implementing or modifying Go code.

## Folder Structure

- `cmd/`: main application entry points, subfolders per entrypoint each with main.go
- `internal/`: core application logic and business rules
- `pkg/`: packages designed to be shared by cmd/ or internal/

## Code Style/Quality

### Naming Conventions

- Package names: short, lower-case, no underscores; indicate purpose not technology
- Avoid redundant type name prefixes that repeat the package name
- Follow Go's initialism standards (use `URL` not `Url`)
- Use MixedCaps (exported) or mixedCaps (unexported); never snake_case
- Receiver names: short (1-2 letters), consistent, never `this` or `self`
- Single-method interfaces use `-er` suffix (e.g. `Reader`, `Writer`)
- Do not prefix getters with `Get`; use `obj.Name()` not `obj.GetName()`
- Avoid generic package names: `util`, `common`, `base`

### Linting

- Write code that passes: ineffassign, staticcheck, go vet
- All code formatted with `gofmt`

## Design Patterns

### Context Propagation

- Accept `context.Context` as first parameter in I/O, RPC, or long-running functions
- Do not store contexts in structs or pass nil
- Use `context.Background()` only at program entry points

### Interfaces

- Keep interfaces small - one or two methods ideal
- Define interfaces at the consumer side, not the provider side
- Accept interfaces, return concrete structs
- Extract interfaces when a second implementation or test fake is needed

### Concurrency

- Document goroutine ownership: who starts it, who stops it
- Protect shared state with `sync.Mutex` or channels - do not mix both
- Use `sync.WaitGroup` to ensure goroutines complete
- Use `go test -race` to catch data races
- Only the sender should close a channel

### HTTP Handler Patterns

- `http.HandlerFunc` for simple handlers
- Middleware as `func(http.Handler) http.Handler`
- Return appropriate HTTP status codes; not 200 for errors
- Set `ReadTimeout`, `WriteTimeout`, `ReadHeaderTimeout` on `http.Server`

### Logging

- Use structured logging with `slog`
- Never log sensitive data
- Use `slog.InfoContext(ctx, ...)` when context is available

### Error Handling

- Use `fmt.Errorf` with `%w` to wrap errors for `errors.Is`/`errors.As`
- Name sentinel errors with `Err` prefix (`ErrNotFound`, `ErrTimeout`)
- Do not overuse panic; restrict to unrecoverable programmer errors

## Test Writing

- Table-driven tests where variation matters
- Keep tests deterministic; avoid `time.Now()` without injection
- Use `t.Helper()` in helper functions
- Use `want`/`got` instead of `expected`/`actual`
- Prefer `t.Parallel()` for top-level tests and sub-tests
- Use gomega package for assertions (see gomega.md)
- Unit tests: `Test{FunctionName}` or `Test{StructName}_{MethodName}`
- Use `t.Context()` instead of `context.Background()` (Go 1.24+)

## Security

- Never put literal secrets in code
- Use `crypto/rand` for security-sensitive randomness; never `math/rand`
- Use parameterized queries for SQL; never concatenate user input
- Run `govulncheck` to scan dependencies
