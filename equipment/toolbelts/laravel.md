# Laravel Toolbelt

## When to Equip

Use when implementing or modifying Laravel models, controllers, migrations,
jobs, or backend/API features in a Laravel (PHP 8.2+) project.

## Folder Structure

When the project has no established layout:

- `app/Http/Controllers/`: thin HTTP handlers
- `app/Http/Requests/`: Form Request validation
- `app/Http/Resources/`: API Resources for responses
- `app/Models/`: Eloquent models
- `app/Policies/`: authorization rules per model
- `app/Jobs/`: queued work
- `app/Services/` or `app/Actions/`: business logic; pick one per project and use it throughout

## Conventions

- **Thin controllers, fat services/actions** - keep HTTP handlers small
- **Form Request classes for validation** - never validate inline in controllers
- **Eloquent for data access** - models in `app/Models`, relationships typed
- **API Resources for responses** - don't return raw models from API endpoints
- **Artisan generators** (`make:model -mfsc`, `make:request`, ...) - follow framework structure
- **PSR-12 + PHP 8.2 features** - typed properties, enums, readonly, constructor promotion
- **Config via `config()` and `.env`** - never call `env()` outside config files

## Implementation Patterns

- [ ] Eager-load relationships (`with()`) to prevent N+1 queries
- [ ] Mass-assignment protection - set `$fillable`; never `$guarded = []`
- [ ] Queue slow work as Jobs; dispatch Events for side effects
- [ ] Authorization via Policies / Gates; authentication via Sanctum (API) or session (web)
- [ ] Schema changes via migrations only; factories and seeders for data
- [ ] Wrap multi-step writes in `DB::transaction()`

## Testing Patterns

- Pest (or PHPUnit) - test-driven; write the test first
- `RefreshDatabase` trait; model factories for fixtures
- Feature tests hit routes via the HTTP test client; unit tests for pure logic
- Assert against the database (`assertDatabaseHas`) and JSON structure
- Run order: static analysis (PHPStan / Larastan) → unit → feature

## Patterns to Avoid

- Business logic in controllers or models - extract to services/actions
- N+1 queries from lazy-loading inside loops
- `env()` calls outside config files (breaks config caching)
- Raw SQL string interpolation - use the query builder and bindings
- Disabling mass-assignment guards (`$guarded = []`)
- Migrations that mix schema changes with data manipulation
- Long `if`/`switch`/`match` chains on a type or kind - use polymorphism (one class per kind behind an interface) or a strategy resolved from the container
