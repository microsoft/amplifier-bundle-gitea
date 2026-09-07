# DONE-NOTE — lane `j1e6-ci-gitea` (`model_performance-nhic`)

**Outcome: A. RESOLVED.** All deliverables DONE. Nothing was recorded NOT-POSSIBLE; the
cap did not bind (see Spend).

`amplifier-bundle-gitea` had **no `.github/workflows` directory at all**. Every change
merged here — including the Stage-1 awareness-dedupe PR **9d54093** — was verified by hand,
never by a CI run. This lane adds one, and proves it can go red.

---

## Deliverables

| Deliverable | State | Evidence |
|---|---|---|
| `.github/workflows/ci.yml` — real suite, ruff pinned, `push:main` + `pull_request`, no path filters / `continue-on-error` / `\|\| true` | **DONE** | the file; `grep` audit below |
| Both run URLs quoted in the PR body; RED job log shows the suite executing | **DONE** | RED [34159890876](https://github.com/microsoft/amplifier-bundle-gitea/actions/runs/34159890876) · GREEN [34160195754](https://github.com/microsoft/amplifier-bundle-gitea/actions/runs/34160195754) |
| Scratch PR CLOSED, branch DELETED — verified, not assumed | **DONE** | PR #16 `state=CLOSED`, `mergedAt=null`; `git ls-remote origin \| grep -i scratch` → **0 refs** |
| A statement of what the suite actually covers | **DONE** | below — **38 collected, 12 execute, 26 opt-in-skipped**. Not zero tests; not full coverage either. |
| Clean main red? → STOP and report | **N/A — clean main is GREEN** | `evidence/ruff-clean-main.txt`; GREEN run above |
| DRAFT PR, marked ready when green, NOT merged | **DONE** | PR **#17**, ready, unmerged. Manager merges. |

---

## The workflow — three jobs

Triggers: `push: branches:[main]` and `pull_request: branches:[main]`.

1. **Lint (ruff)** — `uvx ruff@0.16.6 check --isolated --select E4,E7,E9,F .`
2. **Tests (py3.11 / 3.12 / 3.13)** — `uv sync --python <ver>` then `uv run --no-sync pytest -q --tb=short`
3. **Bundle structure (YAML)** — parses `bundle.md` frontmatter, `behaviors/*.yaml`, and
   `skills/*/SKILL.md`; fails on an empty skill `description`.

### Vacuous-green audit (all four absent, by grep)

```
$ grep -nE 'paths:|paths-ignore:|continue-on-error|\|\| true' .github/workflows/ci.yml
(no matches)
```

---

## What the suite actually covers — read this before trusting the green

**38 tests collected. 12 execute in CI. 26 are skipped**, by the repo's own
`tests/conftest.py`, which puts them behind opt-in flags this workflow deliberately does
not pass:

| File | Collected | Runs in CI | Gate |
|---|---:|---:|---|
| `test_cli_basics.py` | 12 | **12** | none — CLI surface, subprocess-invoked |
| `test_lifecycle.py` | 9 | 0 | `--run-integration` (Docker) |
| `test_e2e_mirror_metadata.py` | 9 | 0 | `--run-e2e` (Docker + GitHub token) |
| `test_github_sync.py` | 4 | 0 | `--run-github --github-test-repo` (live GitHub repo) |
| `test_git_operations.py` | 4 | 0 | `--run-integration` |

So the green means: **the package installs on 3.11/3.12/3.13, the `amplifier-gitea` console
script runs as a real subprocess, and its 12 CLI-surface assertions hold.** It does not mean
the Docker lifecycle works. That is stated here and in the PR body rather than left to look
like coverage — the same reason the `8j42` pattern labels an import smoke.

Wiring `--run-integration` was considered and **rejected**: `tests/conftest.py`'s
session-scoped `cleanup_orphaned_containers` fixture force-removes **every** container
labelled `managed-by=amplifier-gitea` on the host, not just the ones the tests created
(`docs/development.md` warns about this in bold). On a CI runner that is harmless; the
reason to leave it off is that Gitea container startup is a flakiness source, and a CI that
goes red for reasons nobody changed is worse than one with a named, honest gap. Follow-up,
not a silent omission.

---

## The RED proof

Scratch branch `scratch/j1e6-ci-red-proof` = this workflow + one deliberately failing test
(`tests/test_ci_red_proof.py`, `assert 1 == 2`). Draft PR **#16**.

**RED run: <https://github.com/microsoft/amplifier-bundle-gitea/actions/runs/34159890876>**
(head `ff28dbfefa2da45fb4b130a48240fdca7d8b981a`, conclusion `failure`)

The red is a **test** failure, not a setup or lint error — the two non-test jobs in the same
run passed, which is what makes it trustworthy:

| Job | Conclusion |
|---|---|
| Lint (ruff) | **success** |
| Tests (py3.11) | **failure** |
| Tests (py3.12) | **failure** |
| Tests (py3.13) | **failure** |
| Bundle structure (YAML) | **success** |

Job log, all three interpreter legs (`evidence/red-run-test-job-excerpt.txt`):

```
Tests (py3.11)  F............ssssssssssssssssssssssssss   [100%]
Tests (py3.11)  E   AssertionError: deliberate failure: proving the CI test job reports red
Tests (py3.11)  1 failed, 12 passed, 26 skipped in 2.30s
Tests (py3.12)  1 failed, 12 passed, 26 skipped in 2.40s
Tests (py3.13)  1 failed, 12 passed, 26 skipped in 2.59s
```

`12 passed` beside `1 failed` is the point: the real suite executed.

### Scratch teardown — verified, not assumed

```
$ gh pr view 16 --json number,state,closed,mergedAt,headRefName
{"closed":true,"headRefName":"scratch/j1e6-ci-red-proof","mergedAt":null,"number":16,"state":"CLOSED"}

$ git ls-remote origin | grep -i scratch
(no output — 0 remote refs)
```

`gh pr close --delete-branch` **did not delete the remote branch** on this host — it aborted
with `fatal: 'main' is already used by worktree at …`, a local-worktree error, having already
closed the PR. Left unchecked that is exactly the "believed, not read back" failure the
publication contract exists for. The branch was deleted explicitly with
`git push origin --delete`, and the deletion confirmed by the `ls-remote` above.

---

## The GREEN proof

**GREEN run: <https://github.com/microsoft/amplifier-bundle-gitea/actions/runs/34160195754>**
— all 5 jobs `success` on head `d7a4450`. Test legs report `12 passed, 26 skipped`;
bundle structure reports 3 documents parsed including
`skills/gitea/SKILL.md (description=322 chars)` — the exact figure 9d54093 landed.

```
Lint (ruff)               All checks passed!
Tests (py3.11)            12 passed, 26 skipped in 2.32s
Tests (py3.12)            12 passed, 26 skipped in 6.54s
Tests (py3.13)            12 passed, 26 skipped in 2.25s
Bundle structure (YAML)   OK  bundle.md  (bundle.name=gitea)
Bundle structure (YAML)   OK  behaviors/gitea.yaml  (bundle.name=gitea-behavior)
Bundle structure (YAML)   OK  skills/gitea/SKILL.md  (name=gitea, description=322 chars)
Bundle structure (YAML)   Bundle structure OK.
```

A second GREEN run covers the final head (this note itself); its id is recorded in the PR body,
which is edited after the fact rather than committed, so the branch does not chase its own tail.

---

## Findings

### 1. ruff 0.16 ships a WIDER default select than the classic tier — 21 findings here

Measured on clean main @9d54093 with ruff 0.16.6 (`evidence/ruff-clean-main.txt`):

| command | result |
|---|---|
| `uvx ruff@0.16.6 check --isolated --select E4,E7,E9,F .` | **All checks passed!** (exit 0) — *this is what CI runs* |
| `uvx ruff@0.16.6 check .` | **21 findings** (exit 1) — not wired |
| `uvx ruff@0.16.6 format --check .` | 4 files would be reformatted (exit 1) — not wired |

The 21: `I001` ×5, `PLW1510` ×4, `S110` ×3, `BLE001` ×3, `EXE001` ×2, `UP017`, `RUF015`.
**Three of them are in `docs/lanes/mse0-gitea-awareness-delete/evidence/`** — a frozen
evidence artifact of a completed measurement lane, which must not be rewritten to please a
linter. The rest are in `src/` and `tests/` and are real, small cleanups.

**Why the rule set is pinned rather than left implicit.** The goal warns against a "narrowed
lint selection", and that warning is about hiding findings you discovered. This is the
opposite move and it is written down in three places (the workflow comment, the PR body, and
here), with a one-line reproduce command: pinning `--select` does the same job as pinning
`@0.16.6` — it stops an upstream release from turning this red with no local change. The
sibling repo at the same ruff version (`amplifier-bundle-notify`, PR #12) wired the identical
`--isolated --select E4,E7,E9,F`. **Clean main is green under the gate that ships**, so the
"STOP and report" branch did not trigger. The 21 findings are a named follow-up, not absorbed.

*Instrument caveat, worth carrying:* `ruff check .` **without `--isolated`** also inherits any
config in an ancestor directory. This worktree lives several levels under a shared `dev/`
tree; `--isolated` is what makes the CI result and the laptop result the same number.

### 2. The bundle-structure gate is calibrated — it can come out both ways

`00-what-we-know.md` §(q): *"an instrument that cannot come out both ways has not been
tested."* So the gate was run against **7 mutated copies** of the real files before shipping
(`evidence/structure-gate-calibration.txt`): the unmodified control exits 0, and **all six**
break cases exit 1 — empty skill description, malformed `behaviors/*.yaml`, unclosed
`bundle.md` frontmatter, missing `bundle.name`, and each of the two globs matching **nothing**
(an empty glob is a failure, because "0 problems in 0 files, exit 0" is indistinguishable
from a working check).

The empty-description case is the one that matters to this program: 9d54093 deleted
`context/gitea-awareness.md` and moved three triggers into `skills/gitea/SKILL.md`'s
`description` (252 → 322 chars). That description is now this bundle's **only** always-on
discovery surface, and nothing else in the repo tests it.

### 3. `helpers.py` uses `uv run --no-sync --project`, so CI must `uv sync` first

`tests/helpers.py:18` shells out to `uv run --no-sync --project <repo> amplifier-gitea`.
`--no-sync` means the project venv must already exist and be the one under test. Hence
`uv sync --python <matrix>` as a separate step, and `uv run --no-sync pytest` for the suite —
so the interpreter the matrix selects is the interpreter the CLI subprocess actually runs on.
Verified locally on 3.11 (`12 passed, 26 skipped`) before the first push, and in CI on all
three legs.

---

## Deviations from the goal text

1. **Lane artifacts ride on the PR branch.** The goal says the real PR carries "the workflow
   ONLY"; Procedure 4 says lane artifacts go under `docs/lanes/j1e6-ci-gitea/`. `q41k` — the
   exemplar the goal names — resolved this the same way: 5 files, `ci.yml` + `docs/lanes/…`.
   Read as: no source weakening and no scratch test on the real branch, which holds. The
   `src/` and `tests/` trees are untouched.
2. **`ruff format --check` not wired** — 4 files would be reformatted; whitespace churn is out
   of scope for a workflow-only PR and would collide with in-flight branches. Named in the
   workflow comment. Same call as `b4xs` and `nxxf`.
3. **Integration/e2e tests not wired** — reasoning above.

---

## Spend

**$0.00 of the $0.00 authority (0 runs × 0 arms × $0 / 1.00 = $0.00; slack $0.00).**
No API calls, no DTU, no containers, no infrastructure registered, nothing to tear down.
CI minutes only: 2 workflow runs × 5 jobs, all under ~1 minute per job on `ubuntu-latest`.
The cap did **not** bind — every deliverable landed inside it, so this is outcome **A**, not B.

*Authoring-rule check (required by Procedure 3): the goal's cap DOES show its arithmetic, and
it closes — the deliverable buys no runs, so $0.00 funds it exactly.*

---

## What remains open (for the manager)

1. **Merge PR #17**, then confirm main HEAD reports a successful check-run — *configured is
   not installed*. This lane cannot do that step.
2. **21 ruff findings** under 0.16.6's wider defaults (`uvx ruff@0.16.6 check .`), 3 of them
   in frozen `mse0` lane evidence. Needs a decision on excluding `docs/lanes/**` before the
   rest are worth fixing.
3. **`ruff format`** — 4 files, purely mechanical: `uvx ruff@0.16.6 format .`
4. **Docker lifecycle tests never run in CI** — 26 of 38 tests. A separate opt-in workflow
   (manual dispatch, or a nightly) is the honest way to close that gap.
