"""One notice/item-group conversation; scheduling executes its model/search requests."""
from dataclasses import dataclass, field
from copy import deepcopy
import json

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
    instant_output_tokens: int | None = None

    def __post_init__(self):
        if type(self.require_search) is not bool or (self.require_search and self.search_rounds < 1):
            raise ValueError("require_search needs a positive search_rounds limit")
        for name, value in vars(self).items():
            if name == "require_search":
                continue
            if name == "instant_output_tokens" and value is None:
                continue
            minimum = 0 if name in ("search_rounds", "retries") else 1
            if type(value) is not int or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}")
        if self.instant_output_tokens is not None and self.instant_output_tokens > self.output_tokens:
            raise ValueError("instant_output_tokens must not exceed output_tokens")


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


def action_schema(judgment_schema, items, limits, search, search_only=False):
    judgments = _object({key: judgment_schema["properties"][key] for key in items})
    final = _object({"action": {"const": "final"}, "judgments": judgments})
    if not search:
        return final
    query = _object({
        "action": {"const": "search"},
        "queries": {"type": "array", "minItems": 1,
                    "maxItems": limits.queries_per_round,
                    "items": {"type": "string", "minLength": 1, "maxLength": 256}},
    })
    return query if search_only else {"anyOf": [query, final]}


class JudgmentConversation:
    """Own messages, budgets and validation behind the scheduling interface.

    next_turn() supplies a generation request; accept_reply() consumes its reply
    and returns queries when retrieval is needed. Execute those queries (possibly
    pooled with other conversations), then call accept_search() before continuing.
    Token counting uses the injected model, but generation/search never run here.
    Final judgments and trace snapshots are detached from conversation state.
    """
    def __init__(self, task_id, record, items, messages, *, model, item_table,
                 judgment_schema, limits):
        self._state = _Task(task_id, record, tuple(items), deepcopy(messages))
        self.model = model
        self.items = item_table
        self.judgment_schema = judgment_schema
        self.limits = limits
        self._queries = None

    @classmethod
    def _from_task(cls, task, **dependencies):
        """Adapter for historical callers that still own mutable _Task state."""
        conversation = cls(task.task_id, task.record, task.items, [], **dependencies)
        conversation._state = task
        return conversation

    @property
    def task_id(self):
        return self._state.task_id

    @property
    def record(self):
        return self._state.record

    @property
    def done(self):
        return self._state.done

    @property
    def error(self):
        return self._state.error

    @property
    def judgments(self):
        return deepcopy(self._state.judgments)

    def snapshot(self):
        task = self._state
        return deepcopy({"task_id": task.task_id, "items": task.items,
                         "search_rounds": task.rounds,
                         "retrieval_tokens": task.retrieval_tokens, "events": task.trace})

    def _schema(self, search, search_only=False):
        return action_schema(self.judgment_schema, self._state.items, self.limits,
                             search, search_only)

    def _generation_limit(self):
        if (self.limits.instant_output_tokens is not None
                and not getattr(self.model, "thinking", False)):
            return self.limits.instant_output_tokens
        return self.limits.output_tokens

    def next_turn(self):
        if self.done:
            return None
        if self._queries is not None:
            raise RuntimeError("Search results must be supplied before the next turn")
        task = self._state
        tokens = self.model.count_messages(task.messages)
        if tokens + self.limits.output_tokens + 128 > self.model.max_model_len:
            task.error = "Source/conversation exceeds context; no text was truncated"
            task.trace.append({"event": "context_failure", "input_tokens": tokens})
            return None
        # Reserve a complete search action, a result/control message, and final output.
        search = (not task.force_final and task.rounds < self.limits.search_rounds
                  and task.retrieval_tokens < self.limits.total_retrieval_tokens
                  and tokens + 2 * self.limits.output_tokens + 256
                  <= self.model.max_model_len)
        required = self.limits.require_search and task.rounds == 0
        output_tokens = self._generation_limit()
        if required:
            # A search-only action can use a smaller generation budget than final JSON.
            output_tokens = min(output_tokens, self.model.max_model_len - tokens
                                - self.limits.output_tokens - 256)
            if output_tokens < 32:
                task.error = "Required search cannot fit context; no text was truncated"
                task.trace.append({"event": "context_failure", "input_tokens": tokens})
                return None
            search = True
        return Turn(task.task_id, deepcopy(task.messages),
                    self._schema(search, required), output_tokens)

    def accept_reply(self, turn, reply):
        task = self._state
        task.trace.append({"event": "model", "input_tokens": reply.input_tokens,
                           "output_tokens": reply.output_tokens,
                           "finish_reason": reply.finish_reason,
                           "response": reply.text, "error": reply.error,
                           "max_output_tokens": turn.max_tokens,
                           "thinking_tokens": reply.thinking_tokens,
                           "thinking_budget": reply.thinking_budget,
                           "required_search": self.limits.require_search and task.rounds == 0})
        try:
            if reply.error or reply.finish_reason != "stop":
                raise ValueError(reply.error or f"Generation ended: {reply.finish_reason}")
            action = json.loads(reply.text)
            Draft202012Validator(turn.schema).validate(action)
            if action["action"] == "search":
                if any(not query.strip() for query in action["queries"]):
                    raise ValueError("Empty search query")
                task.rounds += 1  # A failed retrieval attempt also consumes one round.
                task.messages.append({"role": "assistant", "content": compact(action)})
                self._queries = {
                    f"{task.task_id}:{task.rounds}:{i}": query
                    for i, query in enumerate(action["queries"])
                }
                return dict(self._queries)
            else:
                self._finish(action["judgments"])
        except (ValueError, TypeError, KeyError, ValidationError) as exc:
            self.reject(exc.message if isinstance(exc, ValidationError) else str(exc))
        return None

    def accept_search(self, hits, error=None):
        if self._queries is None:
            raise RuntimeError("No search is awaiting results")
        task = self._state
        batch = self._queries
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
        self._queries = None

    def reject(self, error):
        """Record an invalid conversation result using the existing retry policy."""
        self._queries = None
        task = self._state
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

    def _finish(self, judgments):
        task = self._state
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

    def replay_judgments(self, task_trace):
        """Revalidate saved successful group output without another model call."""
        finals = [event for event in task_trace['events'] if event['event'] == 'final']
        models = [event for event in task_trace['events'] if event['event'] == 'model']
        if not finals or not models or models[-1]['finish_reason'] != 'stop':
            raise ValueError('Replay requires a successfully completed final response')
        action = json.loads(models[-1]['response'])
        Draft202012Validator(self._schema(False)).validate(action)
        task = self._state
        task.retrieval_tokens = task_trace['retrieval_tokens']
        self._finish(action['judgments'])
        if task.error or not task.trace or task.trace[-1] != finals[-1]:
            raise ValueError('Replayed judgment validation differs from the saved final event')
        return self.judgments
