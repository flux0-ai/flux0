from typing import Any, Dict, Type

import inflection
import pytest
from fastapi import FastAPI, HTTPException, Request
from flux0_api.dependency_injection import resolve_dependency


# Dummy dependency class for testing
class DummyService:
    pass


# A fake container that mimics the Lagom container behavior
class FakeContainer:
    def __init__(self, mapping: Dict[Type[Any], Any]) -> None:
        self.mapping = mapping

    def __getitem__(self, key: Type[Any]) -> Any:
        try:
            return self.mapping[key]
        except KeyError as exc:
            raise Exception(f"Dependency {key.__name__} not found") from exc


def create_dummy_request(app: FastAPI) -> Request:
    """
    Helper function to create a FastAPI Request with a valid ASGI scope and app reference.
    """
    scope = {
        "type": "http",
        "app": app,
    }
    return Request(scope)


def test_resolve_dependency_with_container(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate that Lagom is available.
    monkeypatch.setattr("flux0_api.dependency_injection.LAGOM_AVAILABLE", True)

    app = FastAPI()
    app.state.container = FakeContainer({DummyService: DummyService()})
    request = create_dummy_request(app)

    result = resolve_dependency(request, DummyService)
    assert isinstance(result, DummyService)


def test_resolve_dependency_without_container(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate that Lagom is not available.
    monkeypatch.setattr("flux0_api.dependency_injection.LAGOM_AVAILABLE", False)

    app = FastAPI()
    dummy_instance = DummyService()
    attr_name = inflection.underscore(DummyService.__name__)
    setattr(app.state, attr_name, dummy_instance)

    request = create_dummy_request(app)

    result = resolve_dependency(request, DummyService)
    assert result is dummy_instance


def test_resolve_dependency_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate that Lagom is not available.
    monkeypatch.setattr("flux0_api.dependency_injection.LAGOM_AVAILABLE", False)

    app = FastAPI()
    request = create_dummy_request(app)

    with pytest.raises(HTTPException) as exc_info:
        resolve_dependency(request, DummyService)

    assert exc_info.value.status_code == 500
    assert "DummyService not found" in exc_info.value.detail
