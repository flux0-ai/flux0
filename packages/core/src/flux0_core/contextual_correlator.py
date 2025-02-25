import contextvars
from contextlib import contextmanager
from typing import Iterator

from flux0_core.ids import gen_id


class ContextualCorrelator:
    def __init__(self, delimiter: str = "::", default: str = "<main>") -> None:
        self._instance_id: str = gen_id()
        self._scopes: contextvars.ContextVar[str] = contextvars.ContextVar(
            f"correlator_{self._instance_id}_scopes", default=""
        )
        self._delimiter: str = delimiter
        self._default: str = default

    @contextmanager
    def scope(self, scope_id: str) -> Iterator[None]:
        """
        Enter a new correlation scope.

        Each new scope is appended to the current one using the delimiter.
        When the context exits, the previous scope is automatically restored.
        """
        current: str = self._scopes.get()
        new_scope: str = f"{current}{self._delimiter}{scope_id}" if current else scope_id
        token = self._scopes.set(new_scope)
        try:
            yield
        finally:
            self._scopes.reset(token)

    @property
    def correlation_id(self) -> str:
        """
        Return the current overall correlation string.
        If no scope is active, returns the default value.
        """
        current: str = self._scopes.get()
        return current if current else self._default


# Example usage:
if __name__ == "__main__":
    correlator = ContextualCorrelator()
    print("Default correlation:", correlator.correlation_id)

    with correlator.scope("user"):
        print("Inside 'user' scope:", correlator.correlation_id)
        with correlator.scope("session"):
            print("Inside 'user::session' scope:", correlator.correlation_id)
            with correlator.scope("action"):
                print("Inside 'user::session::action' scope:", correlator.correlation_id)
        print("Back in 'user' scope:", correlator.correlation_id)

    print("After all scopes:", correlator.correlation_id)
