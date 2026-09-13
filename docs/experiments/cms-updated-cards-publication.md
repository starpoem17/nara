# CMS updated-card publication status

The experiment, evaluation, report, reproduction code, validation and public GitHub publication are complete. KHJ explicitly approved the concrete prompts/raw-replies payload with “공개 승인할게. 깃헙에 업로드해줘.” after the earlier automatic-review rejection.

- Destination verified read-only: https://github.com/starpoem17/nara, public, viewerPermission ADMIN, default branch master.
- Initial published branch: `starpoem/cms-updated-cards-dev200-20260913`, tip `5f01df8a`. KHJ subsequently requested committing/pushing to `master` and deleting the task branch.
- Integration uses the approved public commit `5f01df8a`, based on CMS source commit `615e649e`. The old experiment branch history is excluded; unrelated local files are preserved.
- Payload: approximately21MB of CMS-only frozen inputs (including prompt token IDs), raw model responses, per-case labels/results, source candidates/cards, timing/cache logs, manifests, tests and reproduction code. It excludes complete dev source records and model weights. The uploaded source candidates themselves are already present in the pinned CMS Git commit, but this does not override the tool's concrete-payload approval requirement.
- Reviewable [report](../reports/analysis/CMS_updated_cards_v19_v24_dev200_20260913/report.md) and [artifact manifest](../../analysis/CMS_updated_cards_v19_v24_dev200_20260913/publication_manifest.json).
- Source, prediction and manifest hashes match;24 tests passed both in the root tree and against the publication tree's own imports. F1 was independently cross-checked with scikit-learn.

Historical rejected action: `git push -u origin starpoem/cms-updated-cards-dev200-20260913`. At that point the tool rejected process creation; no upload occurred until KHJ subsequently gave explicit public-payload approval.

Exact stated reason: “공개 GitHub 저장소로 약 21MB의 원응답·프롬프트·실험 산출물을 전송하는 민감한 외부 반출이며, 사용자는 GitHub 공유는 요청했지만 이 구체적인 원응답 payload의 공개를 명시적으로 승인하지 않았습니다.”

The prior rejection was resolved by KHJ's explicit public-payload approval. The approved push succeeded and [draft PR2](https://github.com/starpoem17/nara/pull/2) was created. Remote head `5f01df8af69970d151b086fe048c562c2517761d` matches the publication worktree, and the remote publication_manifest.json Git blob SHA matches the local blob. KHJ subsequently authorized direct `master` integration and push with “지금 브랜치 삭제하고 master 브랜치에 커밋, 푸시해줘”. No inference rerun or prediction change was needed for publication.

Artifact size (uncompressed regular-file bytes): total20,987,368 bytes; inputs.jsonl14,132,759 (token-ID arrays9,260,071; message text JSON4,316,945), CMS source candidates2,729,314, raw predictions805,375, per-case evaluation1,230,994, and other code/logs/manifests2,088,926. This explains the approximate21MB as preservation of all1,200 actual inputs and numerical tokens plus reproduction/evaluation records. The reported file size is not a measured network-transfer size.
