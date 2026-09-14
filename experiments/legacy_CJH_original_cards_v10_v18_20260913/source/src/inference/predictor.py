"""Batched, independent judgment conversations with bounded dynamic retrieval."""
from dataclasses import dataclass
from copy import deepcopy
import json
import logging
from pathlib import Path
import time

from nara.inference.conversation import (
    Limits, Turn, Reply, _Task, compact, action_schema, JudgmentConversation,
)


@dataclass
class Prediction:
    record_id: str
    judgments: dict | None
    error: str | None
    trace: list


class Predictor:
    """predict(records, item_groups=None) returns complete results in input order.

    Groups partition item_table exactly once; default is all items in one task.
    Model seam: max_model_len, count_text(text), count_messages(messages),
    generate(list[Turn]) -> {task_id: Reply}. Retrieval seam: search({id: query}).
    Dependencies stay resident; generation and retrieval execute in phases.
    No document truncation, shared record state, or failed-judgment zero filling.
    """

    def __init__(self, model, retriever, item_table, judgment_schema, *, limits=None, legal_criteria=False):
        self.model, self.retriever = model, retriever
        self.items = item_table
        self.criteria = (json.loads(Path(__file__).with_name("legal_criteria.json").read_text(encoding="utf-8"))
                         if legal_criteria else None)
        if self.criteria is not None and not set(item_table) <= set(self.criteria["items"]):
            raise ValueError("Legal criteria do not cover the item table")
        self.judgment_schema = deepcopy(judgment_schema)
        for cell in self.judgment_schema["properties"].values():
            evidence = cell["properties"]["근거문구"]
            if evidence.get("type") != "null":
                evidence["maxLength"] = min(evidence.get("maxLength", 500), 500)
        self.limits = limits or Limits()
        if set(judgment_schema["properties"]) != set(item_table):
            raise ValueError("Item table and judgment schema disagree")
        self.metrics = {}

    def _schema(self, items, search, search_only=False):
        return action_schema(self.judgment_schema, items, self.limits, search, search_only)

    def conversation(self, task_id, record, items):
        return JudgmentConversation(task_id, record, items, self._messages(record, items),
            model=self.model, item_table=self.items, judgment_schema=self.judgment_schema,
            limits=self.limits)

    def _legacy_conversation(self, task):
        return JudgmentConversation._from_task(task, model=self.model, item_table=self.items,
            judgment_schema=self.judgment_schema, limits=self.limits)

    def _finish(self, task, judgments):
        """Compatibility for historical diagnostics; live execution uses conversations."""
        self._legacy_conversation(task)._finish(judgments)

    def _messages(self, record, items):
        rules = "\n".join(
            f"- {key}: {self.items[key]['항목명']}"
            f" ({self.items[key].get('비고', '')})"
            + (" [부재탐지: 근거문구 null]" if self.items[key]["부재탐지"] else "")
            for key in items
        )
        system = (Path(__file__).with_name("prompt.txt").read_text(encoding="utf-8")
                  .replace("{search_rounds}", str(self.limits.search_rounds))
                  .replace("{queries_per_round}", str(self.limits.queries_per_round))
                  + rules)
        if self.criteria is not None:
            parts = ["\n\n항목별 법령 판단 기준", *self.criteria["common"],
                     "약칭: 국가령/국가규칙=국가계약법 시행령/시행규칙, 지방령/지방규칙=지방계약법 시행령/시행규칙, "
                     "정부집행=정부 입찰·계약 집행기준, 지방집행=지방자치단체 입찰 및 계약 집행기준, "
                     "판로법/판로령=중소기업제품 구매촉진 및 판로지원에 관한 법률/시행령, "
                     "SW법=소프트웨어 진흥법, SW지침=중소 소프트웨어사업자의 사업 참여 지원에 관한 지침, "
                     "국가공동=공동계약운용요령, 지방낙찰=지방자치단체 입찰시 낙찰자 결정기준."]
            for key in items:
                rule = self.criteria["items"][key]
                parts.append(f"[{key}] 적용: {rule['applies_if']}\n위반: {rule['violation_if']}"
                             f"\n예외·구별: {rule['exceptions']}\n근거: {'; '.join(rule['references']) or '대조형 항목'}")
                if rule.get("review_note"):
                    parts.append("검토 메모: " + rule["review_note"])
            system += "\n".join(parts)
        if self.limits.require_search:
            system = system.replace("검색은 선택사항이며 이미 판단 가능하면 바로 최종 답한다.",
                                    "최초 응답은 반드시 검색 요청이다. 검색 결과를 받은 뒤 최종 판단한다.")
        # Explicit allowlist: dev labels and other top-level data cannot enter a prompt.
        documents = "\n\n".join(
            f"[{d['type']}:{d['doc_id']}]\n{d['text']}" for d in record["docs"])
        content = (f"[공고 ID] {record['id']}\n[메타]\n" + compact(record["meta"])
                   + "\n[문서]\n" + documents)
        return [{"role": "system", "content": system},
                {"role": "user", "content": content}]


    def predict(self, records, *, item_groups=None):
        records = list(records)
        ids = [record["id"] for record in records]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate record IDs")
        groups = [tuple(group) for group in (
            item_groups if item_groups is not None else [tuple(self.items)])]
        flattened = [key for group in groups for key in group]
        if (not groups or any(not group for group in groups)
                or len(flattened) != len(set(flattened)) or set(flattened) != set(self.items)):
            raise ValueError("Item groups must partition the item table exactly once")
        started = time.monotonic()
        self.metrics = {"model_seconds": 0.0, "retrieval_seconds": 0.0,
                        "model_batches": 0, "retrieval_batches": 0}
        tasks = [self.conversation(f"{ri}:{gi}", record, group)
                 for ri, record in enumerate(records) for gi, group in enumerate(groups)]
        pending, active = iter(tasks), []
        exhausted = False
        while active or not exhausted:
            while len(active) < self.limits.batch_size and not exhausted:
                task = next(pending, None)
                if task is None:
                    exhausted = True
                else:
                    active.append(task)
            requests = []
            for task in active:
                turn = task.next_turn()
                if turn is not None:
                    requests.append(turn)
            if requests:
                tick = time.monotonic()
                try:
                    replies = self.model.generate(requests)
                    if set(replies) != {r.task_id for r in requests}:
                        raise ValueError("Model response IDs differ from request IDs")
                except Exception as exc:
                    replies = {r.task_id: Reply("", error=f"{type(exc).__name__}: {exc}")
                               for r in requests}
                self.metrics["model_seconds"] += time.monotonic() - tick
                self.metrics["model_batches"] += 1
                by_id = {task.task_id: task for task in active}
                searches = {}
                for request in requests:
                    task, reply = by_id[request.task_id], replies[request.task_id]
                    queries = task.accept_reply(request, reply)
                    if queries:
                        searches[task.task_id] = queries
                if searches:
                    self._search(by_id, searches)
            completed = sum(task.done for task in active)
            if completed:
                logging.getLogger(__name__).info("Completed %d/%d judgment tasks",
                                                 sum(task.done for task in tasks), len(tasks))
            active = [task for task in active if not task.done]
        self.metrics["total_seconds"] = time.monotonic() - started
        results = []
        for record in records:
            owned = [task for task in tasks if task.record is record]
            errors = [f"{task.task_id}: {task.error}" for task in owned if task.error]
            judgments = None if errors else {
                key: value for task in owned for key, value in task.judgments.items()}
            results.append(Prediction(record["id"], judgments, "; ".join(errors) or None,
                                      [t.snapshot() for t in owned]))
        return results

    def replay_judgments(self, record, task_trace):
        """Revalidate saved successful output without token counting or generation."""
        conversation = JudgmentConversation('replay', record, task_trace['items'], [],
            model=self.model, item_table=self.items, judgment_schema=self.judgment_schema,
            limits=self.limits)
        return conversation.replay_judgments(task_trace)

    def _search(self, by_id, searches):
        queries = {key: value for batch in searches.values() for key, value in batch.items()}
        tick = time.monotonic()
        error = None
        try:
            hits = self.retriever.search(queries, top_k=self.limits.top_k)
            if set(hits) != set(queries):
                raise ValueError("Retrieval response IDs differ from request IDs")
        except Exception as exc:
            hits, error = {}, f"{type(exc).__name__}: {exc}"
        self.metrics["retrieval_seconds"] += time.monotonic() - tick
        self.metrics["retrieval_batches"] += 1
        for task_id in searches:
            by_id[task_id].accept_search(hits, error)
