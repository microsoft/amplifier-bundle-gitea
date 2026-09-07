# DONE-NOTE — lane `mse0-gitea-awareness-delete`

**Item:** `model_performance-mse0` (STAGE 1 (D): awareness-file dedupe) — **gitea slice only**
**Repo:** `microsoft/amplifier-bundle-gitea`
**Branch:** `lane/mse0-gitea-awareness-delete`
**Merge-base:** `261953d5372ff487d0a9872d914724ef6115e5a0`
**Outcome:** **A — RESOLVED.** All six deliverables DONE. Nothing NOT-POSSIBLE.
**Spend:** **$0.00 of $0.00 authorised.** No API measurement, no DTU, no infrastructure
registered. Every measurement below is a local render or a test run.

---

## 1. Sequencing gate (item's non-negotiable clause) — CLEARED

The item forbids starting on a repo until that repo's `zc6t` PR has merged.

- `zc6t` (`model_performance-zc6t`) is **resolved** (closed 2026-09-07T16:40Z).
- Its own resolution states it shipped **only** the foundation-owned share as
  `amplifier-foundation` PR #372 and shipped every other repo's change as
  out-of-repo patch artifacts, explicitly *not* editing other repos.
- `gh pr list --state all` on this repo shows **no zc6t PR, open or merged**.
  The only open PR is #8 (`feat/idempotent-mirror-from-github`), untouched by
  this lane and touching no file this lane touches.

So zc6t never held this repo, and there is no compression for this change to
land on top of. No conflict is possible. **Gate cleared; not assumed.**

---

## 2. Fact-by-fact classification table (DELIVERABLE 1) — DONE

Every fact in `context/gitea-awareness.md` (629 bytes, merge-base `261953d`),
classified **(a) redundant with a catalog line / tool schema → deleted** or
**(b) an operating rule → MOVED, destination shown**. **No fact silently dropped.**

| # | Fact (verbatim from the file) | Class | Where it lives now |
|---|---|---|---|
| F1 | `# Gitea Environments` | (a) heading, carries no fact | — |
| F2 | "You have access to `amplifier-gitea`, a CLI for on-demand ephemeral Gitea Docker environments." | **(a) redundant** — capability announcement. The `gitea` skill's always-on catalog line is the announcement; the CLI's own name and nature are stated in the skill body. | `hooks-skills-visibility` catalog line (routing) + `skills/gitea/SKILL.md:9` ("`amplifier-gitea` is a CLI for on-demand, ephemeral Gitea Docker containers.") |
| F3 | "Use it for isolated git workflows, safe experimentation, and GitHub mirroring/promoting." | **(a) redundant, EXCEPT "safe experimentation"** which was **absent** from the description and was **MOVED there first** | skill description: "isolated git environment", "mirroring GitHub repos…promoting changes back to GitHub as PRs", **+ new** "git sandbox for experiments/testing/demos" |
| F4 | "User needs an isolated git environment (experiments, testing, demos)" | **(a) redundant for the head clause; the parenthetical was absent → MOVED** | skill description: "isolated git environment" (verbatim, already there) **+ new** "git sandbox for experiments/testing/demos" |
| F5 | "User wants to mirror a GitHub repo, work freely, then promote changes back as a PR" | **(a) redundant** — the description carries this clause almost word for word | skill description: "mirroring GitHub repos for isolated work, or promoting changes back to GitHub as PRs"; triggers "mirror repo", "promote branch" |
| F6 | "User needs a disposable git server with issues, PRs, and API access" | **(a) redundant for "disposable git server" (verbatim in the description); the "issues, PRs, API access" qualifier was absent → MOVED** | skill description: "disposable git server" **+ new** "with issues/PRs/API access". The underlying capability is documented in the skill body at `SKILL.md:59` (Swagger API docs) and `SKILL.md:65` (`--include-issues --include-prs`) |
| F7 | "It will tell you the necessary prerequisites, installation instructions, CLI documentation, workflows, and troubleshooting" | **(a) redundant** — a description of what the skill body contains, which is the skills system's own progressive-disclosure contract, already stated always-on in `skills:context/skills-instructions.md` ("L1 name+description always visible, L2 full body on demand"). The listed sections all exist: prerequisites `SKILL.md:11`, install `SKILL.md:25`, CLI docs `SKILL.md:43`, workflows `SKILL.md:76`, troubleshooting `SKILL.md:103` | `skills-instructions.md` (mechanism) + `skills/gitea/SKILL.md` (the content itself) |
| F8 | ```load_skill(skill_name="gitea")``` | **(a) redundant** — restates the `load_skill` **tool schema**, which is always-on, plus the catalog entry that already names `gitea` as a loadable skill | `load_skill` tool schema + `hooks-skills-visibility` catalog |

### Operating rules in this file: **ZERO**

There is no constraint on how the capability behaves *when used* anywhere in
this file — no ordering rule, no safety rule, no failure-handling rule. Every
operating rule this bundle has already lives in the skill body where it acts
(prerequisites gate `SKILL.md:33` "If prerequisites are missing, report clearly
and stop. Do not attempt workarounds."; the never-mutate-the-source-repo rule
`SKILL.md:101`; token resolution order `SKILL.md:69`). **Nothing needed to move
out of this file except the three missing triggers above.**

Historical note, so a later reader does not think a rule was lost here: the only
rule-shaped lines this file ever had — "You **MUST** load the `gitea` skill as a
**FIRST STEP**" and "If you DO NOT load this skill, you will FAIL and let the
user down :'(" — were deleted in **PR #14** (`261953d`, merged 2026-08-28) with a
measured 5-vs-5 A/B showing they *caused* over-delegation (-27% tree tokens when
removed, 5/5 correctness both arms). They were not silently dropped by this lane
and they are not coming back.

---

## 3. Skill description CONFIRMED to carry every trigger BEFORE the delete (DELIVERABLE 2) — DONE

Full both-sides quoting and the 9-row trigger check:
`evidence/trigger-confirmation.md`.

Summary: **6 of 9 triggers were already carried verbatim. 3 were missing**
("safe experimentation", "(experiments, testing, demos)", "with issues, PRs, and
API access"). **They were moved into the skill description first**, and only then
was the file deleted — the order the item mandates.

- description BEFORE: 252 chars
- description AFTER: 322 chars (**+70**)

Confirmed from a live session's own `hooks-skills-visibility` block that this
description is genuinely always-on — read back from
`sessions/8d973e13-.../events.jsonl`, not assumed.

---

## 4. File deleted, removed from `context.include`, bundle still composes (DELIVERABLE 3) — DONE

Changes (3 files):

1. `context/gitea-awareness.md` — **deleted** (`git rm`); the now-empty `context/`
   directory is gone with it.
2. `behaviors/gitea.yaml` — the whole `context:` block removed (it held exactly one
   entry, `gitea:context/gitea-awareness.md`).
3. `skills/gitea/SKILL.md` — description extended with the 3 missing triggers.

**Composition proof** (`evidence/compose-check.txt`), `load_bundle(strict=True)`
on `./bundle.md`, merge-base worktree vs this branch:

| | BEFORE (`261953d`) | AFTER (this branch) |
|---|---|---|
| composed | OK, exit 0 | OK, exit 0 |
| tools mounted | 1 (`tool-skills`) | 1 (`tool-skills`) |
| pending context includes | 1 | **0** |
| context files contributed | 1 (`gitea:context/gitea-awareness.md`, exists=True) | **0** |

`amplifier bundle show ./bundle.md` also still exits 0 and reports the same
bundle, description and tool.

**A near-miss worth recording** (the exact hazard `KNOWN` warns about — confident,
plausible, wrong output that still exits 0): the first version of
`compose_check.py` read `Bundle.context` directly and reported **0 context files
for the BEFORE tree too**, which would have "proved" the change was a no-op. A
namespaced include is parked in `Bundle._pending_context` and `Bundle.context`
stays empty until `resolve_pending_context()` runs. Caught by checking the claim
against a value already known — the real session demonstrably *did* mount this
file. The script now calls `resolve_pending_context()` and prints both fields.

**No dangling references:** `grep -rn "gitea-awareness"` over tracked files
returns nothing outside the lane's own artifacts.

---

## 5. Real-session head census, before/after, `context_file` count named (DELIVERABLE 4) — DONE

Full output: `evidence/head-census.txt`. Script: `evidence/head_census.py`.

**Method, and its honest limits.** BEFORE is a **real session** — this lane's own
session `8d973e13-a103-4d70-8a57-811d1828e1e8`, whose `mentions:resolved`
(`source=bundle_context`, turn 1) event lists the 23 context files the app bundle
actually mounted, `gitea:context/gitea-awareness.md` among them at position 9.
Those exact resolved paths are then re-rendered through the **shipped** renderer,
`amplifier_foundation.mentions.format_context_block` over a `ContentDeduplicator`
— the same function that produced that session's head. AFTER re-renders the
identical set minus the one path this PR removes. The worktree copy and the cache
copy of the file are byte-identical (`sha256 6b9c2ee7…`), so the render is faithful.

This is a **render measurement, not a second live API session**. The $0 authority
funds "a session render and a head census" and funds no paid run; a live
second session would have cost roughly a dollar of Opus input for a head this
size. Stated plainly rather than passed off as two live sessions.

### The count, stated explicitly

| | `context_file` blocks | rendered head chars |
|---|---|---|
| BEFORE | **23** | 70,371 |
| AFTER | **22** | 69,567 |
| delta | **23 → 22 (−1)** | **−804** |

The −804 chars is the 629-byte file plus its 175-char
`<context_file paths="… → …">` wrapper.

### Net always-on cost, including what was moved in

| Surface | Change |
|---|---|
| `context_file` head block (removed) | **−804 chars** |
| `hooks-skills-visibility` description (3 triggers moved in) | **+70 chars** |
| **Net always-on** | **−734 chars per request, every session** |

Named rather than buried: this change is **not** a pure −804. The move is what
makes the delete safe, and it costs 70 chars.

Item-level context: the item tracks a global `23 → N`. This lane owns **one** of
the 23 blocks; after this PR the head is **22**. The other Stage-1 files are other
lanes' repos and were not touched.

---

## 6. CI (DELIVERABLE 5) — stated plainly

**This repo has no CI.** There is no `.github/workflows/` directory at the
merge-base or on this branch, and no CI configuration of any other kind
(`ls .github/workflows/` → "No such file or directory"). There is therefore no
CI run to be green or red, and no CI check will appear on the PR. Saying so is
the deliverable; there is nothing to fix here and nothing was disabled.

What was run instead, locally:

```
uv run pytest tests/
38 collected — 12 passed, 26 skipped in 2.09s
```

Identical to the merge-base baseline quoted in PR #14 ("12 passed, 26 skipped").
The 26 skips are the Docker/GitHub-token integration and e2e tests, deselected by
default by `tests/conftest.py` — unchanged behaviour, not a regression.

**Default-mode byte-identity** (`evidence/byte-identity.txt`), honestly reported:
`amplifier-gitea --help` is **byte-identical** between the merge-base worktree and
this branch (674 bytes both). `git diff --stat <merge-base> -- src/ tests/
pyproject.toml` is **empty** — no code changed at all. This PR is markdown and
YAML only.

---

## 7. Draft PR (DELIVERABLE 6) — DONE

Draft PR opened against `microsoft/amplifier-bundle-gitea`; the manager merges.
Read-back values are in `DONE.json` under `publication` (`publication/v1`),
obtained from `publication_readback.sh`, not from local `git log`.

---

## Deviations, judgment calls, and anything a reviewer might otherwise trip on

1. **The delete is not a pure delete.** The item said "CONFIRM the skill
   description carries the three triggers, and if it does not, move them there
   BEFORE deleting". It did not carry all of them, so 3 triggers were moved and
   the description grew 70 chars. Doing the delete alone would have been a
   mis-routing bug that surfaces later as "it never suggested gitea".
2. **"The three triggers"** in the item text maps to the file's three
   `## When to Use` bullets. This lane checked at finer grain — 9 distinct trigger
   phrases across the whole file, not 3 bullets — because a bullet can be
   two-thirds covered, which is exactly what happened to bullets 1 and 3.
3. **`docs/` is excluded from awareness accounting**, per the goal's KNOWN note;
   this lane's own artifacts under `docs/lanes/` are never rendered into any
   catalog and cost 0 always-on bytes.
4. **The `context/` directory is now gone**, not left empty. Nothing else lived in it.
5. **Custody was lost once mid-lane and re-established.** `work_status` returned
   `holding: null` and the item had gone back to `open` with `holder: null`
   (background renewal is one-strike). Caught by checking rather than assuming,
   re-claimed with `work_claim(item_id=...)`, no work lost, nothing double-claimed.
6. **Nothing outside this repo was touched**, and no other repo was edited. No
   infrastructure was created, so there is nothing in the infra ledger to tear
   down and `lane_teardown.sh` was not run (no rows to claim). `infra_ledger.sh
   sweep` was never invoked.

## Spend ledger

| Item | Authorised | Spent |
|---|---|---|
| API measurement | $0.00 (explicitly not authorised) | **$0.00** — none run |
| DTU / infrastructure | $0.00 | **$0.00** — none created |
| **Total** | **$0.00** | **$0.00** |

The cap never bound: every deliverable was reachable with local renders, a test
run and text edits, which is exactly what the $0 authority contemplates. This is
outcome branch **A**, not B.
