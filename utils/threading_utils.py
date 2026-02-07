"""Background task runner with poll-based UI updates (no event queue flooding)."""

import threading
from typing import Callable, Any, Optional


class BackgroundTask:
    """Run a function in a background thread.

    The background thread writes to shared state; the UI polls it.
    Only the final on_complete / on_error fires a single after() event.
    """

    def __init__(
        self,
        root_widget,
        task_fn: Callable,
        on_complete: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        self.root = root_widget
        self.task_fn = task_fn
        self.on_complete = on_complete
        self.on_error = on_error
        self._cancelled = False
        self._finished = False

    def start(self):
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()

    def cancel(self):
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    @property
    def is_finished(self) -> bool:
        return self._finished

    def _run(self):
        try:
            result = self.task_fn(cancelled=lambda: self._cancelled)
            self._finished = True
            if not self._cancelled and self.on_complete:
                self.root.after(0, self.on_complete, result)
        except Exception as e:
            self._finished = True
            if self.on_error:
                self.root.after(0, self.on_error, e)
