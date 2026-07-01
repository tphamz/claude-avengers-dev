# Compliance Gadget

## When to Equip

Use when reviewing plans or code handling sensitive data, user information,
or systems subject to regulatory requirements.

## Review Criteria

- [ ] Data classification - sensitive data (PII, PCI, PHI) identified and labeled?
- [ ] Access controls - access to sensitive data restricted?
- [ ] Audit trail - data access and modifications logged with who/what/when?
- [ ] Data retention - defined retention policy? Deletion automated?
- [ ] Encryption at rest - sensitive data encrypted in storage?
- [ ] Encryption in transit - TLS enforced?
- [ ] Data masking - sensitive fields masked in logs and non-prod?
- [ ] Data minimization - only necessary data collected?

## Patterns to Flag

- PII logged in plain text
- Sensitive data in URL query parameters
- Missing encryption on financial or personal data columns
- Missing access controls on admin or data export endpoints
- Audit logs that don't capture the actor

## Reference

- SOC 2 Trust Service Criteria
- PCI-DSS
- GDPR data protection principles
