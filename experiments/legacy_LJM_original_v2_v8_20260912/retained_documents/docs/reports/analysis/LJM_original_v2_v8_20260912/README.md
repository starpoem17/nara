# LJM 원본 실험 검토 안내

주최 측 검증셋 200개에 LJM의 두 코드를 독립적으로 적용한 단일 실행 기록이다. 성공 기준이나 채택·기각 결론을 두지 않았다. Gemma 800회는 모두 실행됐으며 787개 판정을 집계하고 단일 JSON 판독 규칙을 통과하지 못한 13개는 별도로 남겼다.

1. [실행 조건과 전체 결과](report.md): 후보 스캐너 v2~v8, 원본 추출기 + Gemma v4~v7의 결과를 구분한다.
2. [원본 코드가 실제로 하는 일](original_behavior.md): 원본 규칙·후보 의미·프롬프트·추출 제한을 확인한다.
3. [법령 발췌 방식과 출처](law_selection.md): 한글 원문, 연결 조항, 삭제 허용 범위, 실제 토큰 수를 확인한다.
4. [스캐너 사례 검토](scanner_review.md)와 [전체 오탐·미탐](scanner_cases.md).
5. Gemma 항목별 전체 정답 양성·모델 양성·판정 실패 사례: [v4](cases_v4.md), [v5](cases_v5.md), [v6](cases_v6.md), [v7](cases_v7.md).

6. 모델 설명 검토: [v4·v5](gemma_v4_v5_review.md), [v6·v7](gemma_v6_v7_review.md).
7. [응답 형식과 판독 실패 13개 원문](response_format.md).

## 실제 입출력

- [전체 800개 입력 메시지](../../../../analysis/LJM_original_v2_v8_20260912/extractor/requests.jsonl)
- [원본 추출 JSON 200개](../../../../analysis/LJM_original_v2_v8_20260912/extractor/extracted.jsonl)
- [모델 원응답](../../../../analysis/LJM_original_v2_v8_20260912/extractor/responses.jsonl)
- [800개 판정과 모든 설명 필드 CSV](../../../../analysis/LJM_original_v2_v8_20260912/extractor/judgments.csv)
- [원본 후보 스캐너 출력](../../../../analysis/LJM_original_v2_v8_20260912/scanner/candidate_v2_v8.csv)
- [점수와 실행 집계](../../../../analysis/LJM_original_v2_v8_20260912/evaluation.json)
- [원본·프롬프트·법령 일치 검증](../../../../analysis/LJM_original_v2_v8_20260912/verification.json)
- [고정 설정과 파일 해시](../../../../analysis/LJM_original_v2_v8_20260912/manifest.json)

기존 변형 실험의 결과는 [철회 안내](../../ljm-v2-v8-summary/README.md)로 대체했다. 이번 모델 입력에는 기존 프로젝트 프롬프트·법령 해석 초안·후보 스캐너 출력이 들어가지 않는다. LJM 프롬프트의 검색 요청 문구만 합의대로 바꾸고 제공 패키지의 법령 원문을 첨부했다.
