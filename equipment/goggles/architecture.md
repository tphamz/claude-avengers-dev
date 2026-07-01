# Architecture Goggles

## When to Equip

Use when exploring system boundaries, module organization, or API surface area.
Best for understanding how a codebase is structured before major changes.

## Exploration Strategy

1. **Map the boundaries** - entry points, public APIs, external integrations
2. **Trace the dependency graph** - follow imports from top-level modules down
3. **Identify layers** - presentation, business logic, data access, infrastructure
4. **Find the contracts** - interfaces, types, schemas defining module boundaries
5. **Spot the patterns** - factory, repository, service, controller, middleware
6. **Check for violations** - circular dependencies, layer-skipping, god modules

## Focus Areas

- [ ] Project structure - directory layout, module organization, naming
- [ ] Entry points - where does execution begin?
- [ ] Dependency direction - do dependencies flow inward toward core logic?
- [ ] Module boundaries - clearly separated responsibilities?
- [ ] Shared state - where is global state? How is it managed?
- [ ] Configuration - how is the app configured?
- [ ] Error propagation - how do errors flow to user-facing response?
- [ ] Data flow - how does data enter, transform, and exit the system?

## What to Report

- Architectural diagram (text-based) showing major modules
- Layer breakdown with key files for each layer
- Dependency direction analysis - clean or problematic
- Boundary violations or coupling concerns
- Entry point map with file:line references

## Reference

- Clean Architecture: dependency rule, layers, boundaries
- Hexagonal Architecture: ports and adapters
- Domain-Driven Design: bounded contexts, aggregates
