# Trigger confirmation — BEFORE the file was deleted

Both sides quoted verbatim. The awareness file's triggers are on the left; the
covering `gitea` skill description (always-on via `hooks-skills-visibility`) is
on the right. Two triggers were **missing** and were **MOVED into the skill
description first**; the file was deleted only after that.

## Side A — `context/gitea-awareness.md` at merge-base `261953d` (629 bytes, verbatim)

```markdown
# Gitea Environments

You have access to `amplifier-gitea`, a CLI for on-demand ephemeral Gitea Docker environments. Use it for isolated git workflows, safe experimentation, and GitHub mirroring/promoting.

## When to Use

- User needs an isolated git environment (experiments, testing, demos)
- User wants to mirror a GitHub repo, work freely, then promote changes back as a PR
- User needs a disposable git server with issues, PRs, and API access

## How to Use

It will tell you the necessary prerequisites, installation instructions, CLI documentation, workflows, and troubleshooting:

```
load_skill(skill_name="gitea")
```
```

## Side B — `skills/gitea/SKILL.md` frontmatter description

### BEFORE (merge-base `261953d`, 252 chars) — verbatim

```yaml
description: Use when managing ephemeral Gitea Docker environments, mirroring GitHub repos for isolated work, or promoting changes back to GitHub as PRs. Triggers on gitea, ephemeral git, isolated git environment, mirror repo, promote branch, disposable git server.
```

### AFTER (this branch, 322 chars, +70) — verbatim

```yaml
description: Use when managing ephemeral Gitea Docker environments, mirroring GitHub repos for isolated work, or promoting changes back to GitHub as PRs. Triggers on gitea, ephemeral git, isolated git environment, git sandbox for experiments/testing/demos, mirror repo, promote branch, disposable git server with issues/PRs/API access.
```

## Trigger-by-trigger check

| # | Trigger in the awareness file (verbatim) | Present in the BEFORE description? | Action |
|---|---|---|---|
| T1 | "isolated git workflows" | **YES** — "for isolated work" and "isolated git environment" | none needed |
| T2 | "safe experimentation" | **NO** — no experiment/sandbox word anywhere | **MOVED** → "git sandbox for experiments/testing/demos" |
| T3 | "GitHub mirroring/promoting" | **YES** — "mirroring GitHub repos", "promoting changes back to GitHub as PRs", "mirror repo", "promote branch" | none needed |
| T4 | "User needs an isolated git environment" | **YES** — "isolated git environment", verbatim | none needed |
| T5 | "(experiments, testing, demos)" | **NO** — none of the three words present | **MOVED** → "git sandbox for experiments/testing/demos" |
| T6 | "mirror a GitHub repo, work freely, then promote changes back as a PR" | **YES** — "mirroring GitHub repos for isolated work, or promoting changes back to GitHub as PRs" | none needed |
| T7 | "a disposable git server" | **YES** — "disposable git server", verbatim | none needed |
| T8 | "with issues, PRs, and API access" | **NO** as a routing trigger (the capability itself is documented in the skill BODY at `SKILL.md:59` — Swagger API docs — and `SKILL.md:65` — `--include-issues --include-prs`) | **MOVED** → "disposable git server with issues/PRs/API access" |
| T9 | word "gitea" / "`amplifier-gitea`" | **YES** — "gitea" is the first trigger term; `amplifier-gitea` contains it | none needed |

**Result: 6 of 9 triggers were already carried verbatim; 3 were missing and were
moved into the description before the delete.** Nothing routes through the
deleted file that does not now route through the always-on skill description.

## The description really is always-on — read back from a live session

Not assumed. Pulled from the same real session's own event stream
(`sessions/8d973e13-.../events.jsonl`), the `hooks-skills-visibility` catalog
block carries the description **verbatim**:

```
- **gitea**: Use when managing ephemeral Gitea Docker environments, mirroring GitHub repos for isolated work, or promoting changes back to GitHub as PRs. Triggers on gitea, ephemeral git, isolated git environment, mirror repo, promote branch, disposable git server.
```

(That is the pre-change text, because the session predates this branch. It is
the proof that whatever the description says is on every turn of every session.)

## Why the description is the right destination

`hooks-skills-visibility` injects every skill's `name` + `description` into the
head of every session — the same always-on surface the deleted file occupied.
The description is therefore not a cheaper place for a trigger; it is the
*single* place, which is the point of the change. Net always-on cost of the
move: **+70 chars**, against **-804 chars** removed. See `head-census.txt`.
