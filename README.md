# Avengers Dev

An Avengers-themed agentic workflow plugin for Claude Code. Avengers, assemble!

## Installation

Avengers Dev installs as a Claude Code **plugin**. Install it through the plugin
system — **do not hand-edit `settings.json`**. The marketplace `source` schema is
easy to get wrong; let Claude Code write it for you.

**From a local clone** (recommended while developing):

```
/plugin marketplace add /path/to/avengers-dev
/plugin install avengers-dev@avengers-dev
```

**From GitHub:**

```
/plugin marketplace add https://github.com/tphamz/claude-avengers-dev
/plugin install avengers-dev@avengers-dev
```

**Quick, non-persistent** (testing only — evaporates on restart, creates no
marketplace registration):

```bash
claude --plugin-dir /path/to/avengers-dev
```

Then **restart Claude Code** — plugin agents, skills, and hooks are loaded at
session start, not hot-reloaded.

### Verify the install

- **`/doctor`** → the **Plugin errors** section should be clean (or absent).
- **`/agents`** → the five Avengers appear as `avengers-dev:blackwidow`, `:thor`,
  `:captain`, `:hulk`, `:vision`.
- Type **`/avengers-dev:`** → the skills autocomplete.

> **Namespacing (important):** plugin skills and agents are addressed as
> `avengers-dev:<name>` — e.g. `/avengers-dev:bmad`, `Agent(avengers-dev:blackwidow)`.
> Bare `/bmad` or `blackwidow` will **not** resolve.

## Setup

**Per-project persona.** Run **`/avengers-dev:avengers-init`** inside a project to
activate the IronMan persona and orchestration rules (writes `.claude/rules/` and
the `.avengers/` state directory). Restart or reload so the rules take effect.

**BMAD-METHOD dependency** — only needed for **`/avengers-dev:bmad`**. The BMAD
conductor *wraps* the real BMAD-METHOD framework, whose skills require a
project-level install. In the repo you want to run a BMAD sequence against:

```bash
npx bmad-method install   # one-time, interactive — creates the project's _bmad/ config
```

`/avengers-dev:bmad` preflights this and stops with instructions if `_bmad/` is
missing, so it never fails mid-sequence.

**BMAD tracks & knowledge base.** Run `/avengers-dev:bmad <name> [quick|standard|full]`
(default `standard`):

- **quick** — `bmad-quick-dev` plus a Captain review, for small changes.
- **standard** — Brief → PRD → Architecture → Epics/Stories → Spec Hardening →
  Readiness → hard gate → Sprint → Build → Review.
- **full** — standard plus ATDD (`bmad-testarch-atdd`) before each build and a
  requirement-to-test trace (`bmad-testarch-trace`) in review. Needs the BMAD TEA
  module (`_bmad/tea/`).

Every track starts with a knowledge-base (KB) check and ends with a KB refresh
check. The KB (`bmad-document-project` index + `bmad-generate-project-context`) is
built only when missing, offered for refresh when stale, and refreshed after
breaking or otherwise impactful changes. Its freshness marker is
`.avengers/kb.json`.

## The Avengers Squad

| Agent          | Role                | When to Use                                          |
| -------------- | ------------------- | ---------------------------------------------------- |
| **IronMan**    | Orchestrator        | Multi-step tasks, coordination, BMAD sequences       |
| **BlackWidow** | Spy / Explorer      | Codebase exploration, pattern discovery, bug tracing |
| **Thor**       | Builder             | Writing code, implementing features, fixing bugs     |
| **Captain**    | Sentinel / Reviewer | Code reviews, quality analysis, security             |
| **Hulk**       | Engineer            | Plan review, pre-flight checks, test coverage        |
| **Vision**     | BMAD Conductor      | Conducts the real BMAD-METHOD through the crew (quick / standard / full tracks) |

## Equipment System

| Agent      | Equipment | Available                                              |
| ---------- | --------- | ------------------------------------------------------ |
| Captain    | Lenses    | `security`, `performance`, `ui-ux`, `adversarial`      |
| Thor       | Toolbelts | `react`, `python`, `go`, `nestjs`, `laravel`           |
| BlackWidow | Goggles   | `architecture`, `detective`                            |
| Hulk       | Gadgets   | `deployment`, `compliance`                             |
| IronMan    | Schemes   | `avengers-assemble`, `rescue-mission`, `bmad-sequence` |

## Skills

All skills are namespaced — invoke as `/avengers-dev:<name>`:

- **`/avengers-dev:avengers-init`** - Activate the persona + orchestration rules in a project
- **`/avengers-dev:bmad [name] [quick|standard|full]`** - Conduct the real BMAD-METHOD through the crew on a chosen track (needs `npx bmad-method install`; see Setup)
- **`/avengers-dev:avengers-test`** - Test runner (auto-detects Jest, pytest, Go test, etc.)
- **`/avengers-dev:avengers-split`** - Quick health check
- **`/avengers-dev:avengers-ssl`** - SSL certificate bundle for proxy environments
- **`/avengers-dev:avengers-checkpoint`** / **`:avengers-resume`** / **`:avengers-log`** - Session state
- **`/avengers-dev:avengers-vibes`** - Avengers-themed spinner verbs

Type `/avengers-dev:` in the prompt to browse the full list.

## License

MIT

---

*"I am Iron Man." - Tony Stark*
