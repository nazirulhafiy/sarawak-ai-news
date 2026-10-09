# Continuous integration

## Build workflow

The **build** workflow (`.github/workflows/build.yml`) runs tests, audits, a static
build, and (on `main` pushes) GitHub Pages deploy.

### Concurrency

- **Pull requests:** `test-build` uses a per-PR concurrency group
  (`build-<PR number>`) with `cancel-in-progress`, so new commits on the same PR
  cancel an older run on that PR only. Different PRs do not cancel each other.
- **`main` pushes and deploy:** `deploy` uses a shared `pages` group with
  `cancel-in-progress: false`, so a Pages deploy (including after the daily story
  push) is never cancelled mid-flight by another workflow run.

`test-build` on `main` uses a ref-based group without cancel-in-progress so PR
activity cannot cancel production builds.

## Docs check

Pull requests run the **docs check** workflow (`.github/workflows/docs-check.yml`) on
`opened`, `synchronize`, `reopened`, `labeled`, and `unlabeled` events.

The check watches only design and behavior sources, not editorial content:

- `site/**/*.css`
- `site/**/*.js`
- `site/fonts/**`
- `scripts/build.py` (HTML page structure and markup are templated here)

It does **not** watch `data/`, generated `dist/` output, or other content files, so
daily news ingestion and publication are not blocked by this gate.

### Pass and fail

- If the pull request changes any watched file **and** changes nothing under `docs/`,
  the check fails with a message to update `docs/design.md` (or another doc under
  `docs/`) or to add the `no-docs-needed` label.
- If the pull request includes changes under `docs/`, the check passes.
- If the pull request has the `no-docs-needed` label, the check passes even when
  watched files change without `docs/` updates.

The workflow creates the `no-docs-needed` label in the repository when it is missing.

Logic lives in `scripts/docs_check_pr.py` for local debugging:

```bash
DOCS_CHECK_BASE=origin/main DOCS_CHECK_HEAD=HEAD python3 scripts/docs_check_pr.py
```

Set `GITHUB_EVENT_PATH` to a saved pull-request event JSON when testing label bypass
locally.
