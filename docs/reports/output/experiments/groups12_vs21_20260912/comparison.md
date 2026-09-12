Artifacts: [run directory](<../../../../../output/experiments/groups12_vs21_20260912>). Unlinked artifact names below are relative to that directory.

# Twelve vs twenty-one groups

One timed dev200 pass per configuration; 12 then 21; separate engines; cache reset after smoke; startup excluded; retries/recovery included.

Same current sources, dev200 order, rule items v2/v3/v22, OFF mode, output2048, engine16, scheduling and recovery policy. Singleton order follows the existing groups. Each run includes an untimed first8 smoke.

| Metric | 12 groups | 21 groups |
|---|---:|---:|
| prediction_seconds | 313.8189718670001 | 326.1243768429995 |
| model_turns | 2402 | 4201 |
| search_rounds | 0 | 0 |
| output_tokens | 120636 | 144273 |
| input_tokens | 27506789 | 47937934 |
| cached_fraction | 0.9076485081555684 | 0.9463009398778012 |
| invalid_responses | 2 | 1 |
| recovery_seconds | 0.0 | 0.0 |
| macro_f1 | 0.2869096815183057 | 0.26398982003846677 |
| micro_f1 | 0.22380106571936056 | 0.1693227091633466 |
| false_positives | 347 | 766 |
| false_negatives | 90 | 68 |
| label_accuracy | 0.9089583333333333 | 0.82625 |

Time change: +12.305s (+3.92%).
Changed judgments: 713; corrected 158; regressed 555.

## Per item

| Item | Name | F1 12 | F1 21 | Delta | FP 12→21 | FN 12→21 | Changed |
|---|---|---:|---:|---:|---:|---:|---:|
| v1 | 참가자격 특정기관 제한 | 0.375000 | 0.222222 | -0.152778 | 6→9 | 4→5 | 8 |
| v2 | 고시금액 미만 실적제한 | 0.933333 | 0.933333 | +0.000000 | 1→1 | 0→0 | 0 |
| v3 | 실적제한 1배수 이상 | 1.000000 | 1.000000 | +0.000000 | 0→0 | 0→0 | 0 |
| v4 | 고시금액 이상 특정기관, 특정실적 | 0.500000 | 0.307692 | -0.192308 | 3→27 | 3→0 | 27 |
| v5 | 고시금액 이상 지역제한 | 0.526316 | 0.300000 | -0.226316 | 7→10 | 2→4 | 11 |
| v6 | 고시금액 미만 지역제한 시,군,구 | 0.222222 | 0.119403 | -0.102819 | 10→57 | 4→2 | 53 |
| v7 | 고시금액 미만 지역제한 인접 확대 | 0.333333 | 0.424242 | +0.090909 | 3→19 | 5→0 | 21 |
| v8 | 중복제한 (실적+지역) | 0.275862 | 0.333333 | +0.057471 | 19→9 | 2→3 | 13 |
| v9 | 과업지시서 특정 모델명 명시 | 0.312500 | 0.387097 | +0.074597 | 21→19 | 1→0 | 9 |
| v10 | 중기간 경쟁제품 입찰 직생 없음 | 0.060606 | 0.092308 | +0.031702 | 25→55 | 6→4 | 44 |
| v11 | 중기간 경쟁제품 입찰 중소 없음 | 0.000000 | 0.063158 | +0.063158 | 10→178 | 6→0 | 174 |
| v12 | 일반제품 직생 제한 | 0.000000 | 0.230769 | +0.230769 | 0→40 | 6→0 | 46 |
| v13 | 중기간 경쟁제품 소기업, 소상공인 제한 | 0.000000 | 0.000000 | +0.000000 | 0→21 | 6→6 | 21 |
| v14 | 고시금액 이상 일반물품 중소기업 제한 | 0.121212 | 0.000000 | -0.121212 | 23→18 | 6→8 | 21 |
| v15 | 1억 이상- 고시금액미만 소기업 제한 | 0.000000 | 0.000000 | +0.000000 | 5→5 | 6→6 | 6 |
| v16 | 1억 이상- 고시금액미만 중소기업 제한 없음 | 0.125000 | 0.062500 | -0.062500 | 9→118 | 5→2 | 116 |
| v17 | 1억원 미만 일반물품 중소기업 제한 | 0.000000 | 0.100000 | +0.100000 | 19→13 | 6→5 | 25 |
| v18 | 1억원 미만 일반물품 소기업 제한 없음 | 0.200000 | 0.217391 | +0.017391 | 29→34 | 3→2 | 38 |
| v19 | 물품공급 확약서 입찰 시 제출 | 0.500000 | 0.333333 | -0.166667 | 6→14 | 2→2 | 12 |
| v20 | 입찰참가자격 (SW) | 0.222222 | 0.000000 | -0.222222 | 3→2 | 4→5 | 4 |
| v21 | 공동 5% (10%) | 0.000000 | 0.000000 | +0.000000 | 0→0 | 6→6 | 0 |
| v22 | 현장설명회 참석업체 (자격으로 제한 여부) * 계약방법 협상만 적용 | 1.000000 | 1.000000 | +0.000000 | 0→0 | 0→0 | 0 |
| v23 | 현장설명회 (공고기간) * 계약방법 협상 + 계약법 지방만 적용 | 0.067114 | 0.066116 | -0.000998 | 139→112 | 0→1 | 58 |
| v24 | 공고서와 나라장터 입력값 상이 | 0.111111 | 0.142857 | +0.031746 | 9→5 | 7→7 | 6 |

Single run per condition: no estimate of timing variance or order effects. Dev accuracy is descriptive, not holdout validation. F1 averages all24items, including zero-support items as zero. Scheduling can alter outputs; this measures the complete grouping change under fixed policy.

Artifacts: comparison.json, per_item_comparison.csv, changed_judgments.csv; each run contains manifests, source snapshots, predictions, traces and evaluation.
