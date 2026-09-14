"""Wait for every submitted request before releasing a batch to the predictor."""
from nara.inference.continuous import ContinuousPredictor


class BatchCompletionModel:
    """Preserve submit order and hold early completions until the whole batch ends."""
    def __init__(self, model):
        self.model = model
        self.order = []
        self.completed = {}

    def __getattr__(self, name):
        return getattr(self.model, name)

    @property
    def thinking(self):
        return self.model.thinking

    @thinking.setter
    def thinking(self, value):
        self.model.thinking = value

    def submit(self, turn):
        self.model.submit(turn)
        self.order.append(turn.task_id)

    def poll(self):
        for task_id, reply in self.model.poll():
            self.completed[task_id] = reply
        if len(self.completed) < len(self.order):
            return []
        if set(self.completed) != set(self.order):
            raise ValueError('Batch response IDs differ from submitted task IDs')
        replies = [(task_id, self.completed[task_id]) for task_id in self.order]
        self.order.clear()
        self.completed.clear()
        return replies

    def abort(self):
        self.model.abort()
        self.order.clear()
        self.completed.clear()


class BatchedPredictor(ContinuousPredictor):
    """Same group/mode/cache/retry pipeline with a barrier after each model batch."""
    def __init__(self, model, *args, **kwargs):
        super().__init__(BatchCompletionModel(model), *args, **kwargs)
