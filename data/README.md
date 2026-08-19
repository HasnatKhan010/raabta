# RAABTA data directory

Large or licensed datasets are not committed. `sample/articles.jsonl` is clearly marked synthetic fixture text for automated tests only. It must never contribute to reported metrics or the user-facing knowledge base.

## Layout

- `raw/`: explicitly downloaded source subsets (Git-ignored)
- `processed/`: generated article/passages and metadata (Git-ignored except documentation)
- `sample/`: tiny synthetic fixtures
- `diagnostic/schema.csv`: empty annotation template for the student-curated diagnostic set

## Diagnostic annotation contract

The diagnostic set must contain 150–200 manually verified underlying questions, including answerable and out-of-corpus cases. The required specification fields are present, plus `split`, `annotator`, and `verification_status` audit fields. Gold evidence must be copied exactly from the frozen corpus. Query authors must not see the final test gold passage while authoring QueryBridge rules.

Allowed `verification_status` progression: `draft`, `project_verified`, `human_verified`. This assignment evaluates only `project_verified` development records and labels them accordingly. Splits are assigned once and stored, not regenerated during experiments.

## Source and license notes

- Wikimedia Wikipedia `20231101.ur`: dataset metadata declares CC BY-SA 3.0 and GFDL. Preserve article URL/title and comply with attribution/share-alike requirements before redistributing processed passages.
- Mavkif Roman-Urdu-Parl-split: dataset metadata declares Apache-2.0. The acquisition script refuses missing or unexpected license metadata.

The project-specific domain field is a deterministic heuristic label for corpus balancing. It is not presented as an official Wikipedia category.
