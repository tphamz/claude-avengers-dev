# Deployment Gadget

## When to Equip

Use when reviewing plans for changes that will be deployed - new features,
configuration updates, or dependency upgrades.

## Review Criteria

- [ ] Rollback plan - can this change be safely rolled back?
- [ ] Backward compatibility - will existing clients break during rollout?
- [ ] Database migrations - are they backward-compatible?
- [ ] Feature flags - should this be behind a flag for gradual rollout?
- [ ] Configuration changes - new env vars documented with safe defaults?
- [ ] Dependency versions - new dependencies pinned?
- [ ] Canary criteria - what metrics to monitor during gradual rollout?

## Risk Assessment

- **Zero-downtime**: Can this be deployed without service interruption?
- **Data safety**: Could this corrupt or lose data if partially applied?
- **Blast radius**: How many users/services are affected if this fails?
- **Recovery time**: How long to detect and recover from a bad deployment?

## Patterns to Flag

- Schema migrations that drop columns without a deprecation period
- Hard dependency on new configuration without defaults
- Breaking API changes without versioning
- Large deployments without a canary plan
