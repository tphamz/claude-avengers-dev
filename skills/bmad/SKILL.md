---
name: bmad
description: >
  Initiate or resume a BMAD (Build More Architect Dreams) sequence via Vision.
  Runs the full 8-phase methodology: Assessment -> Brief -> Requirements ->
  Technical Design -> Planning -> Delivery Readiness -> Sprint -> Implementation -> Review.
allowed-tools: Agent, Bash, Read
argument-hint: "[sequence-name] [resume]"
---

# BMAD - Build More Architect Dreams

## Steps

### 1. Parse Arguments

- **No argument**: Prompt user for a sequence name. Names should be kebab-case, descriptive. Example: "payment-gateway", "auth-modernization", "mobile-redesign".
- **`[sequence-name]`**: Initiate a new BMAD sequence with that name.
- **`[sequence-name] resume`** or **`resume [sequence-name]`**: Resume an existing sequence.
- **`resume`** (no name): List available sequences and prompt for selection.

### 2. Check for Existing Sequence

```bash
ls .avengers/relay-sequences/bmad-*.yaml 2>/dev/null
```

If a sequence matching the name exists, ask: "A BMAD sequence named '{name}' already exists. Resume it?"

### 3. Dispatch to Vision

```
Agent(vision) with the scheme bmad-sequence and the sequence name.
```

The Vision agent handles the full relay. IronMan's role is to:
- Dispatch Vision
- Present Vision's deliverables to the user at each phase boundary
- Provide the design-implementation boundary authorization (Phase 5 -> Phase 6 hard gate)
- Handle escalations from Vision

### 4. Phase Boundary Handling

At each phase completion, Vision surfaces its announcement. IronMan presents it to
the user and waits for confirmation before telling Vision to continue.

The **design-implementation boundary** (Phase 5 -> Phase 6) is a hard gate.
Present the Delivery Readiness Report to the user. Require explicit "[1] Continue
into implementation" or "[2] Exit" choice before Vision proceeds.
