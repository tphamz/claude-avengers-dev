# Performance Lens

## When to Equip

Use when reviewing data-intensive operations, database queries, API endpoints,
or any code where latency, throughput, or resource usage matters.

## Focus Areas

- [ ] Algorithm complexity - O(n^2) or worse where O(n log n) is achievable
- [ ] N+1 query patterns - loops issuing individual DB queries
- [ ] Missing database indexes on WHERE, JOIN, ORDER BY columns
- [ ] Unbounded queries - missing LIMIT/pagination on large result sets
- [ ] Memory leaks - unclosed connections, event listeners, growing caches
- [ ] Unnecessary data fetching - SELECT \* when specific columns needed
- [ ] Caching opportunities - repeated expensive computations
- [ ] Synchronous blocking - blocking I/O on hot paths
- [ ] Bundle size - unnecessary imports, large dependencies for small features
- [ ] Rendering performance - unnecessary re-renders, missing memoization
- [ ] Connection pooling - new connections per request instead of reusing

## Patterns to Flag

- Nested loops over collections O(n\*m) where a lookup map would suffice
- Database queries inside loops
- Missing pagination on list endpoints
- Synchronous file I/O on request paths
- Unbounded in-memory caches without eviction policy
- Repeated computation of the same value in a loop

## Reference

- Big-O complexity analysis
- Database query planning and EXPLAIN output
- Web Vitals: LCP, FID, CLS
