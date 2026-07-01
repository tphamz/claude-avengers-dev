# Detective Goggles

## When to Equip

Use when tracing bugs, investigating unexpected behavior, or tracking down
state mutations. Best for "why is this happening?" questions.

## Investigation Strategy

1. **Start at the symptom** - what is the observable wrong behavior?
2. **Identify the data** - what value is wrong? What should it be?
3. **Trace backward** - follow the data from the symptom to its origin
4. **Find the mutation** - where does the data change from correct to incorrect?
5. **Check the assumptions** - what does the code assume that might not be true?
6. **Verify the fix point** - confirm root cause explains all observed symptoms

## Focus Areas

- [ ] Reproduce path - exact sequence that triggers the bug
- [ ] Data flow - trace the problematic value from input to output
- [ ] State mutations - where is shared state modified? Race conditions?
- [ ] Boundary crossings - data format changes at module boundaries?
- [ ] Timing issues - async race conditions, event ordering
- [ ] Error swallowing - exceptions caught and silently ignored?
- [ ] Recent changes - what changed since last known-good state?

## What to Report

- Root cause with file:line reference
- The exact point where behavior diverges
- The chain of events from trigger to symptom
- Contributing factors with file:line references
- Suggested fix approach
- Regression test strategy
