# Feature legal criteria

Assets: [criteria JSON](<../../src/inference/legal_criteria.json>), [original human review](<../maintenance/evidence/structure-migration/original_reports/docs/reports/analysis/feature_legal_criteria_v1.md>), [full system prompt](<evidence/legal-criteria/legal_criteria_v1_system_prompt.txt>).

- `nara --legal-criteria` opts into `Predictor(..., legal_criteria=True)`. Load the static JSON once; append common rules and only the assigned items. Existing defaults and source documents remain intact. Package the JSON as part of the installed `nara` package when enabled.
- Derived from supplied snapshot and item table only, without dev labels. JSON records original-source paths and SHA-256; review document includes original item-table mappings. No external legal data.
- Draft interpretations: v3 uses statutory >1x/추정가격, conflicting with item title ≥1x/사업예산; v5 lacks the referenced 지방 행안부 고시 amount; v14–18 follow the linked statute's goods/services scope. No claim of official scoring interpretation.
- No inference experiment with these criteria yet. 26 unit tests pass, covering source provenance, item coverage, group scoping, input isolation and existing RAG behavior; they do not validate legal truth or accuracy.

## Context preflight

Use `uv run --locked python -m nara.tools.check_legal_criteria --output tmp/TASK_ID/context.json` for a fresh check. The old renderer mixed fixed historical observations with current criteria, so its source is retained with the original diagnostic evidence rather than exposed as a maintained command.

[Measured report](<evidence/legal-criteria/legal_criteria_v1_context.json>): thinking template, 200 dev notices, 32768 context, initial prompts only, reserve output +128. With output 2048, group sizes 24/6/1 fail 22/5/0 notices; with output 4096 they fail 28/15/7. Maximum inputs: 35761/31714/30553. Group size 1 requires 4800 initial tasks and leaves minimum 39 tokens with output 2048. Retrieval/retries are not certified by this check. Compress criteria or design long-document handling before treating the enriched prompt as a full-run configuration.

See [dynamic RAG](<dynamic-rag.md>) for inference protocol and context semantics.

[Original aggregate evidence](<../maintenance/evidence/structure-migration/original_reports/docs/reports/analysis/feature_legal_criteria_v1.md>); historical measurements are preserved as source material.
