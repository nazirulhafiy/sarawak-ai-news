# Continuous integration

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
