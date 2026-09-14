"""Batched, independent judgment conversations with bounded dynamic retrieval."""
from dataclasses import dataclass, field
from copy import deepcopy
import json
import logging
from pathlib import Path
import time

from jsonschema import Draft202012Validator, ValidationError


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


@dataclass(frozen=True)
class Limits:
    batch_size: int = 8
    search_rounds: int = 2
    queries_per_round: int = 4
    top_k: int = 5
    round_tokens: int = 4096
    total_retrieval_tokens: int = 8192
    output_tokens: int = 2048
    retries: int = 1
    require_search: bool = False

    def __post_init__(self):
        if type(self.require_search) is not bool or (self.require_search and self.search_rounds < 1):
            raise ValueError("require_search needs a positive search_rounds limit")
        for name, value in vars(self).items():
            if name == "require_search":
                continue
            minimum = 0 if name in ("search_rounds", "retries") else 1
            if type(value) is not int or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")


@dataclass(frozen=True)
class Turn:
    task_id: str
    messages: list
    schema: dict
    max_tokens: int


@dataclass(frozen=True)
class Reply:
    text: str
    finish_reason: str = "stop"
    input_tokens: int = 0
    output_tokens: int = 0
    error: str | None = None
    thinking_tokens: int = 0
    thinking_budget: int | None = None


@dataclass
class Prediction:
    record_id: str
    judgments: dict | None
    error: str | None
    trace: list


@dataclass
class _Task:
    task_id: str
    record: dict
    items: tuple
    messages: list
    rounds: int = 0
    retrieval_tokens: int = 0
    seen: set = field(default_factory=set)
    retries: int = 0
    force_final: bool = False
    judgments: dict | None = None
    error: str | None = None
    trace: list = field(default_factory=list)

    @property
    def done(self):
        return self.judgments is not None or self.error is not None


def _object(properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


class Predictor:
    """predict(records, item_groups=None) returns complete results in input order.

    Groups partition item_table exactly once; default is all items in one task.
    Model seam: max_model_len, count_text(text), count_messages(messages),
    generate(list[Turn]) -> {task_id: Reply}. Retrieval seam: search({id: query}).
    Dependencies stay resident; generation and retrieval execute in phases.
    No document truncation, shared record state, or failed-judgment zero filling.
    """

    def __init__(self, model, retriever, item_table, judgment_schema, *, limits=None):
        self.model, self.retriever = model, retriever
        self.items = item_table
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
        judgments = _object({key: self.judgment_schema["properties"][key] for key in items})
        final = _object({"action": {"const": "final"}, "judgments": judgments})
        if not search:
            return final
        query = _object({
            "action": {"const": "search"},
            "queries": {"type": "array", "minItems": 1,
                        "maxItems": self.limits.queries_per_round,
                        "items": {"type": "string", "minLength": 1, "maxLength": 256}},
        })
        return query if search_only else {"anyOf": [query, final]}

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
        tasks = [_Task(f"{ri}:{gi}", record, group, self._messages(record, group))
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
                tokens = self.model.count_messages(task.messages)
                if tokens + self.limits.output_tokens + 128 > self.model.max_model_len:
                    task.error = "Source/conversation exceeds context; no text was truncated"
                    task.trace.append({"event": "context_failure", "input_tokens": tokens})
                    continue
                # Reserve a complete search action, a result/control message, and final output.
                search = (not task.force_final and task.rounds < self.limits.search_rounds
                          and task.retrieval_tokens < self.limits.total_retrieval_tokens
                          and tokens + 2 * self.limits.output_tokens + 256
                          <= self.model.max_model_len)
                required = self.limits.require_search and task.rounds == 0
                output_tokens = self.limits.output_tokens
                if required:
                    # A search-only action can use a smaller generation budget than final JSON.
                    output_tokens = min(output_tokens, self.model.max_model_len - tokens
                                        - self.limits.output_tokens - 256)
                    if output_tokens < 32:
                        task.error = "Required search cannot fit context; no text was truncated"
                        task.trace.append({"event": "context_failure", "input_tokens": tokens})
                        continue
                    search = True
                requests.append(Turn(task.task_id, task.messages,
                                     self._schema(task.items, search, required), output_tokens))
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
                    task.trace.append({"event": "model", "input_tokens": reply.input_tokens,
                                       "output_tokens": reply.output_tokens,
                                       "finish_reason": reply.finish_reason,
                                       "response": reply.text, "error": reply.error,
                                       "max_output_tokens": request.max_tokens,
                                       "thinking_tokens": reply.thinking_tokens,
                                       "thinking_budget": reply.thinking_budget,
                                       "required_search": self.limits.require_search and task.rounds == 0})
                    try:
                        if reply.error or reply.finish_reason != "stop":
                            raise ValueError(reply.error or f"Generation ended: {reply.finish_reason}")
                        action = json.loads(reply.text)
                        Draft202012Validator(request.schema).validate(action)
                        if action["action"] == "search":
                            if any(not query.strip() for query in action["queries"]):
                                raise ValueError("Empty search query")
                            task.rounds += 1  # A failed retrieval attempt also consumes one round.
                            task.messages.append({"role": "assistant", "content": compact(action)})
                            searches[task.task_id] = {
                                f"{task.task_id}:{task.rounds}:{i}": query
                                for i, query in enumerate(action["queries"])
                            }
                        else:
                            self._finish(task, action["judgments"])
                    except (ValueError, TypeError, KeyError, ValidationError) as exc:
                        self._retry(task, exc.message if isinstance(exc, ValidationError) else str(exc))
                if searches:
                    self._retrieve(by_id, searches)
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
                                      [{"task_id": t.task_id, "items": t.items,
                                        "search_rounds": t.rounds,
                                        "retrieval_tokens": t.retrieval_tokens,
                                        "events": t.trace} for t in owned]))
        return results

    def _retry(self, task, error):
        task.trace.append({"event": "invalid_response", "error": error[:300]})
        if task.retries >= self.limits.retries:
            task.error = "Response invalid after retries: " + error[:300]
            return
        task.retries += 1
        required = self.limits.require_search and task.rounds == 0
        task.force_final = not required
        # Discard invalid generated text; preserve the original and all successful retrievals.
        task.messages[-1] = {
            **task.messages[-1],
            "content": task.messages[-1]["content"] +
            ("\n이전 출력은 유효하지 않았다. 반드시 유효한 검색 요청 JSON을 작성하라." if required else
             "\n이전 출력은 유효하지 않았다. 추가 검색 없이 지정한 모든 항목의 최종 JSON을 완성하라.")
        }

    def _finish(self, task, judgments):
        if self.limits.require_search and task.retrieval_tokens == 0:
            task.error = "Required search yielded no passages in context"
            return
        documents = [doc["text"] for doc in task.record["docs"]]
        dropped = []
        for key, value in judgments.items():
            evidence = value["근거문구"]
            if value["위반여부"] == 0 or self.items[key]["부재탐지"]:
                evidence = None
            elif evidence and (evidence.startswith(("=", "+", "@"))
                               or not any(evidence in text for text in documents)):
                dropped.append(key)
                evidence = None
            value["근거문구"] = evidence
        task.judgments = judgments
        task.trace.append({"event": "final", "evidence_dropped": dropped})

    def _retrieve(self, by_id, searches):
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
        for task_id, batch in searches.items():
            task = by_id[task_id]
            remaining = self.limits.search_rounds - task.rounds
            instruction = (f"남은 검색 횟수: {remaining}. 필요하면 검색어를 보완하거나 최종 판단하라."
                           if remaining else "검색 한도에 도달했다. 확보한 자료로 반드시 최종 판단하라.")
            header = "법령 검색 결과 (판정 참고 자료이며 근거문구 인용 대상이 아님):\n"
            tail = "\n" + instruction
            if error:
                tail = "\n검색 실패. 검색 실패 자체로 위반을 판단하지 말라.\n" + instruction
            budget = min(self.limits.round_tokens,
                         self.limits.total_retrieval_tokens - task.retrieval_tokens)
            selected, new_keys = [], set()
            # Round-robin rank order prevents the first query consuming the entire text budget.
            ranked = [hits.get(key, []) for key in batch]
            for rank in range(max(map(len, ranked), default=0)):
                for row in ranked:
                    if rank >= len(row):
                        continue
                    hit = row[rank]
                    key = " ".join(hit.text.split())
                    if key in task.seen or key in new_keys:
                        continue
                    passage = {"passage_id": hit.passage_id, "source": hit.source,
                               "locator": hit.locator, "title": hit.title,
                               "section": hit.section, "text": hit.text}
                    candidate = selected + [passage]
                    body = compact(candidate)
                    message = {"role": "user", "content": header + body + tail}
                    if (self.model.count_text(body) > budget
                            or self.model.count_messages(task.messages + [message])
                            + self.limits.output_tokens + 128 > self.model.max_model_len):
                        continue
                    selected, new_keys = candidate, new_keys | {key}
            body = compact(selected)
            # Empty result has no retrieved material; control text is still context-budgeted.
            used = self.model.count_text(body) if selected else 0
            task.seen.update(new_keys)
            task.retrieval_tokens += used
            task.messages.append({"role": "user", "content": header + body + tail})
            task.trace.append({"event": "search", "round": task.rounds, "queries": batch,
                               "passage_ids": [p["passage_id"] for p in selected],
                               "tokens": used, "error": error,
                               "remaining_rounds": remaining})
