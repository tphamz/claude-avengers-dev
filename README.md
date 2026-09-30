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
`.avengers/kb.json` (or `<workstation>/avengers/kb.json` with an md workstation),
keyed per branch.

## md Workstation

Keep a repo's markdown out of the code repo — for example in one central md repo
that holds the docs for many code repos. Run **`/avengers-dev:avengers-workstation`**
(also offered by `avengers-init` and on every `/avengers-dev:bmad` run). The first
time, it asks for an md root; the workstation is `<md-root>/<repo-name>-mds/`. Later
runs, other clones and other worktrees find it automatically, and it asks again
only if the folder is gone.

- **How:** BMAD's `output_folder` (`_bmad-output`) becomes a directory symlink to
  the workstation, ignored through `.git/info/exclude`. BMAD config stays relative,
  so the committed config is still portable for the team, and every `bmad-*`
  skill follows the link.
- **What lands there:** BMAD planning and implementation artifacts,
  `project-context.md`, Hulk specs (`avengers/specs/stories/`), and the KB marker
  (`avengers/kb.json`). Per-clone relay state stays in `.avengers/`.
- **Keys outside the output folder** (usually `project_knowledge: {project-root}/docs`)
  stay in the repo unless you opt in, per key, to re-point them. Re-pointing edits
  the team's committed `_bmad/*/config.yaml`; a declined key is not asked again.
- **Existing `_bmad-output`:** `migrate` moves it into the workstation. If it is
  tracked in git, `migrate --untrack` is required — once that removal is committed
  and pushed, every teammate who pulls loses their working copy, so agree with the
  team first.
- **md commits:** at the end of discovery, at the design gate and at completion,
  the relay offers to commit the workstation's changes in its md repo, touching
  only that repo's folder. Nothing is ever pushed.
- **Searching:** default `rg`, `grep -r` and `find` (and so a root-level search) do
  not follow the `_bmad-output` symlink. `.claude/rules/avengers-kb.md` tells agents
  where the markdown lives and to search by explicit path (`_bmad-output/...` or
  the workstation path) or with `grep -R` / `find -L`.
- **md commits** warn first when the workstation's git repo is not a dedicated md
  repo (your home directory, or a repo that contains the project).
- **Forks:** the registry (`~/.avengers/workstations.json`) is keyed by the
  normalized remote URL (`origin`, else `upstream`), so a fork gets its own entry.
  A folder-name clash suggests `<org>-<repo>-mds`.
- **Limitation:** `bmad-story-automator` rejects artifact paths that resolve outside
  the repo root, so it does not work with a workstation. The Avengers relay does
  not use it. macOS and Linux only (directory symlinks).

`/avengers-dev:avengers-uninstall` removes the symlink, exclude lines and directory
grant, and keeps the workstation contents.

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
- **`/avengers-dev:avengers-workstation [status|set|root|migrate|unlink]`** - External md workstation for Avengers + BMAD markdown
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
