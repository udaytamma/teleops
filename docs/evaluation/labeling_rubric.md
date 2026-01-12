# Manual Labeling Rubric

This rubric is used to score RCA outputs against labeled cases.

## Scoring (0.0 - 1.0)
- 1.0: Root cause matches the labeled cause with equivalent specificity.
- 0.7: Root cause is correct but less specific (same subsystem, missing exact component).
- 0.4: Root cause is adjacent (same layer or symptom-focused, but not causal).
- 0.0: Root cause is unrelated or missing.

## Evidence Alignment (Optional Addendum)
- +0.1 bonus if evidence cites the relevant device or interface.
- +0.1 bonus if the remediation aligns with the labeled cause.

## Notes
- Score the best hypothesis when multiple are returned.
- If multiple labels apply, score against the primary label.
