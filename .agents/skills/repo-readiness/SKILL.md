---
name: repo-readiness
description: Evaluate whether a repository is ready for AI-assisted development using a deterministic local score, then explain gaps and guide improvements.
---

# Repo Readiness

Use this skill when a user asks whether a repository is ready for AI-assisted development, wants a readiness audit, or needs help improving the repository's development context.

## Non-negotiable boundary

The score belongs to the script. Do not calculate, adjust, infer, or replace it in prose. Run `scripts/score_repo.py` against the repository and treat its JSON output as the sole source of the score, band, passed checks, failed checks, weights, and recommendations.

The script evaluates repository artifacts only. A passing check means the expected artifact or signal exists; it does not prove the artifact is correct, secure, or high quality. Explain that limitation when presenting results.

## Workflow

1. Identify the repository root. Use the user-provided path when one is given; otherwise use the current repository.
2. Run:

   ```bash
   python3 scripts/score_repo.py --repo /absolute/path/to/repository
   ```

   Run it from this skill directory or use the absolute path to the script. Keep the JSON output intact for interpretation.
3. Report the script's `score`, `max_score`, and `band` exactly. Explain the band using the `band_meaning` value from the output; do not invent thresholds.
4. Summarize passed and failed checks using their names and evidence. For failed checks, use the script's `improvement` text.
5. Recommend the highest-impact improvements by descending `weight`, then by the script's existing recommendation order. Do not reorder based on personal preference or alter the score.
6. Separate objective findings from qualitative observations. If an artifact exists but appears weak, say that the deterministic check passed and offer a qualitative follow-up separately.
7. Do not modify the repository during an audit unless the user asks. If the user asks to create missing artifacts, confirm which artifacts to create when the request is broad, then make focused changes and rerun the scorer.

## Response shape

Keep the result easy to scan:

- score and band from the script;
- what the score means, using `band_meaning`;
- failed checks ordered by impact;
- the smallest useful next steps;
- an offer to create selected missing artifacts.

When a user asks for a rerun after changes, execute the script again rather than comparing scores manually.

## Script contract

`scripts/score_repo.py` uses only the Python standard library and emits deterministic JSON. It accepts `--repo` and optional `--pretty`. Its output includes:

- `score`, `max_score`, and `band`;
- `band_meaning`;
- ordered `checks`, each with an id, name, weight, passed state, evidence, and improvement;
- `recommendations`, containing failed checks in impact order.

Do not add checks that require network access, package installation, model judgment, timestamps, or nondeterministic directory ordering. If the rubric changes, update the script and its user-facing explanation together.
