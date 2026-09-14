Artifacts: [run directory](<../../../../../output/experiments/v9-cod-off512-20260912>). Unlinked artifact names below are relative to that directory.

# Interpretation: OFF CoD on actual dev200

Primary operational finding: candidate not suitable to replace both items. Short synthetic legal probe did not transfer reliably to long Korean notices: only18/200 first outputs have all notes <=5 whitespace words (bullets stripped; labels counted). Mean notes242.15 tokens, mean first output304.88, vs directOFF58.045 total.

Results must distinguish parser policies. As-executed pipeline rejected fencedJSON, causing avoidable retries; six terminal errors were recovered from saved schema-valid stopped responses, yielding v9 F1.363636 (TP2 FP3 FN4), v19 .545455 (TP3 FP2 FN3). This is predictions.csv. Corrected parser replay selects chronological first valid stopped JSON, stripping only outer fences, never changing keys/labels/quotes: predictions_first_valid.csv, v9 .307692 (TP2 FP5 FN4), v19 .666667 (TP4 FP2 FN2). All200 covered in both; no zero-filling. This replay is not a newly timed engine run. Example035 first valid fenced response correctly flags v19, but unnecessary retry reverses it.

Historical directOFF v9 .444444 (TP6 FP15 FN0), v19 .363636 (TP2 FP3 FN4). Original12group .370370/.470588; basicON .400000/.400000; CoDON .416667/.526316. v9 recall loss matters: misses09/050/051/052; old051 TP already had unrelated evidence. Genuine source restriction TP12 quoted, TP23 lacks quote. Supplier assurance wrongly attributed to v9 e.g037: lexical quote fidelity is not semantic evidence correctness.

Measured execution388.620s vs direct152.521s,285 model responses,21 length stops,91 invalid-response events (includes validation retries). Output91546 vs11609 tokens, including retries. Report.json retains six original failed IDs; revalidation.json resolves them. Do not call388.620s corrected-parser latency or attribute full overhead to CoD; invalid fence handling inflated retries. No searches.

This candidate combines synthetic few-shot, notes, and unconstrained decoding, while old pipeline constrainedJSON. v19 improvement is encouraging but not an isolated CoD effect. Do not adopt forv9. Consider separate v19 follow-up only with corrected parser and controlled few-shot comparison; no further experiments performed here.
