# NestJS Toolbelt

## When to Equip

Use when implementing or modifying NestJS modules, controllers, providers,
guards, interceptors, or backend features in a NestJS (TypeScript/Node) project.

## Conventions

- **Modular architecture** - one feature module per domain; import modules, don't reach across them
- **Constructor dependency injection** - inject providers via the constructor; never `new` a service
- **DTOs validated with `class-validator` / `class-transformer`** for every request body, query, and param
- **Global `ValidationPipe`** with `whitelist: true` and `forbidNonWhitelisted: true`
- **Config through `@nestjs/config`** - no `process.env` reads outside the config module
- **Naming**: `*.module.ts`, `*.controller.ts`, `*.service.ts`; `PascalCase` classes, one provider per file

## Implementation Patterns

- [ ] Thin controllers - HTTP concerns only; business logic lives in services
- [ ] Guards for authn/authz (Passport / JWT), not inline checks in handlers
- [ ] Interceptors for cross-cutting concerns (logging, serialization, timeouts)
- [ ] Exception filters with `HttpException` subclasses for consistent error responses
- [ ] Data access behind a provider (TypeORM or Prisma) - inject the repository, don't query in controllers
- [ ] `async/await` throughout; never leave a floating promise

## Testing Patterns

- Jest with `@nestjs/testing` `Test.createTestingModule`
- Unit-test services with mocked providers (`.useValue` / `.useMocker`)
- e2e tests via `supertest` against a booted `INestApplication`
- Run in order: typecheck → unit → integration → e2e
- Mock external I/O (DB, HTTP) at the provider boundary

## Patterns to Avoid

- Circular module dependencies - extract shared code into a third module before reaching for `forwardRef()`
- Business logic in controllers
- Reading `process.env` directly instead of the config service
- Fat `useFactory` providers - keep DI wiring thin
- Skipping DTO validation on "internal" endpoints
- Deep pure-TypeScript typing or DB-query tuning - defer those to a specialist pass
