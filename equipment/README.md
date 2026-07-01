# Agent Equipment System

The equipment system lets IronMan customize each Avenger's focus for a task.

## Equipment Types

| Agent      | Equipment     | Purpose                    | Available                                              |
| ---------- | ------------- | -------------------------- | ------------------------------------------------------ |
| Captain    | **Lenses**    | Focus reviews              | `security`, `performance`, `ui-ux`, `adversarial`      |
| Thor       | **Toolbelts** | Implementation conventions | `react`, `python`, `go`, `nestjs`, `laravel`                                |
| BlackWidow | **Goggles**   | Exploration strategy       | `architecture`, `detective`                            |
| Hulk       | **Gadgets**   | Domain review criteria     | `deployment`, `compliance`                             |
| IronMan    | **Schemes**   | Orchestration workflows    | `avengers-assemble`, `rescue-mission`, `bmad-sequence` |

## How It Works

Name the equipment in the Agent() dispatch prompt. Each agent has `Skill(equip-*)` in
their `tools:` list - they invoke the equip skill themselves via the Skill tool.

## Parallel Equipping

IronMan can dispatch multiple instances of the same agent with different equipment
concurrently: one Captain with security lens + one Captain with performance lens, both reviewing simultaneously.
