import os
from typing import Any, Dict, List, Tuple

import pytest

# Import the modules under test
from LLD.evaluator import DesignEvaluator
from LLD.models import ClassDesign


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
class _FakeParsed:
    """Mimic the object returned by ``client.responses.parse`` in the OpenAI SDK."""

    def __init__(self, data: Dict[str, Any]):
        # The real object exposes the parsed data through ``output_parsed`` which
        # itself has a ``dict()`` method. We reproduce just enough of that surface
        # to satisfy the evaluator implementation.
        class _OutputParsed:
            def __init__(self, _data: Dict[str, Any]):
                self._data = _data

            def dict(self) -> Dict[str, Any]:  # noqa: D401
                return self._data

        self.output_parsed = _OutputParsed(data)


class _FakeResponses:
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    # The evaluator calls ``parse`` with some keyword arguments. We accept **kwargs
    # to stay future-proof.
    def parse(self, *_, **__) -> _FakeParsed:  # noqa: D401
        return _FakeParsed(self._data)


class _FakeClient:
    """Extremely small stub to replace the real OpenAI client during tests."""

    def __init__(self, data: Dict[str, Any]):
        self.responses = _FakeResponses(data)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure mandatory environment variables are present during tests."""

    # The evaluator checks for an API key at import-time. We inject a dummy one so
    # the constructor does not raise.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-key")
    # Keep temperature/model consistent to avoid unrelated issues.
    monkeypatch.setenv("OPENAI_TEMPERATURE", "0.0")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")


@pytest.fixture()
def _patched_evaluator(monkeypatch: pytest.MonkeyPatch) -> DesignEvaluator:
    """Return a DesignEvaluator whose OpenAI dependency is fully stubbed."""

    mocked_output: Dict[str, Any] = {
        "overall_score": 8.5,
        "feedback": [("good", "Looks solid overall")],
        "suggestions": ["Maybe add docstrings for public methods"],
        "design_patterns": ["Factory"],
    }

    # Replace ``OpenAI`` class with a lambda returning our fake client.
    monkeypatch.setattr(
        "LLD.evaluator.OpenAI", lambda: _FakeClient(mocked_output), raising=True
    )

    return DesignEvaluator()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_evaluate_class_design_returns_expected_schema(
    _patched_evaluator: DesignEvaluator,
) -> None:
    """The high-level evaluation must return the exact structure we expect."""

    design = ClassDesign(
        name="UserService",
        responsibilities=["Manage user accounts"],
        attributes=["_users", "_db_conn"],
        methods=["create_user", "delete_user"],
        relationships=["uses Database"],
    )

    result = _patched_evaluator.evaluate_class_design(design)

    # Basic shape assertions
    assert set(result.keys()) == {
        "overall_score",
        "feedback",
        "suggestions",
        "design_patterns",
    }
    assert isinstance(result["overall_score"], (int, float))
    assert isinstance(result["feedback"], list) and all(
        isinstance(item, tuple) and len(item) == 2 for item in result["feedback"]
    )
    assert isinstance(result["suggestions"], list)
    assert isinstance(result["design_patterns"], list)


def test_srp_evaluation_scores_correctly(monkeypatch: pytest.MonkeyPatch) -> None:
    """_evaluate_srp should give the maximum score for a single responsibility."""

    # Patch OpenAI so we can instantiate the evaluator but won't use it here.
    monkeypatch.setattr("LLD.evaluator.OpenAI", lambda: _FakeClient({}), raising=True)
    evaluator = DesignEvaluator()

    single_resp = ClassDesign(
        name="Logger",
        responsibilities=["Log messages"],
        attributes=[],
        methods=[],
        relationships=[],
    )

    score, feedback = evaluator._evaluate_srp(single_resp)
    assert score == 10
    assert feedback and feedback[0][0] == "good"


def test_encapsulation_detects_private_attributes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("LLD.evaluator.OpenAI", lambda: _FakeClient({}), raising=True)
    evaluator = DesignEvaluator()

    design = ClassDesign(
        name="Account",
        responsibilities=["Store account information"],
        attributes=["_balance", "_owner"],
        methods=["get_balance", "set_balance"],
        relationships=[],
    )

    score, feedback = evaluator._evaluate_encapsulation(design)
    # Expect at least the base score for detecting getters/setters + private attrs
    assert score >= 13
    # Ensure we have at least one "good" feedback entry
    assert any(level == "good" for level, _ in feedback)


def test_abstraction_names_methods_well(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("LLD.evaluator.OpenAI", lambda: _FakeClient({}), raising=True)
    evaluator = DesignEvaluator()

    design = ClassDesign(
        name="CartService",
        responsibilities=["Manage shopping cart"],
        attributes=["_items"],
        methods=[
            "add_item",
            "remove_item",
            "update_item",
            "get_total",
        ],
        relationships=[],
    )

    score, feedback = evaluator._evaluate_abstraction(design)
    assert score >= 8
    assert any(level == "good" for level, _ in feedback)


# ---------------------------------------------------------------------------
# Optional live-API test
# ---------------------------------------------------------------------------
@pytest.mark.skipif(
    os.getenv("OPENAI_API_KEY") in (None, ""),
    reason="No OPENAI_API_KEY set – skipping live OpenAI integration test.",
)
def test_live_evaluate_class_design_returns_expected_schema() -> None:
    """Hit the real OpenAI API to ensure JSON schema parsing still works.

    This test is executed only when a valid ``OPENAI_API_KEY`` environment variable
    is present. It invokes the evaluator end-to-end (no mocks) and asserts that
    the response structure matches what the application expects.  We *do not*
    assert on the exact content because LLMs are non-deterministic; we only check
    that the required keys and types exist.
    """

    evaluator = DesignEvaluator()

    design = ClassDesign(
        name="PaymentService",
        responsibilities=["Process payments"],
        attributes=["_gateway", "_transactions"],
        methods=["create_payment", "refund"],
        relationships=["uses Gateway"],
    )

    result = evaluator.evaluate_class_design(design)

    assert set(result.keys()) == {
        "overall_score",
        "feedback",
        "suggestions",
        "design_patterns",
    }
    assert isinstance(result["overall_score"], (int, float))
    assert isinstance(result["feedback"], list)
    assert isinstance(result["suggestions"], list)
    assert isinstance(result["design_patterns"], list)
