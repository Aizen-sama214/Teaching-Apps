from typing import Dict, List, Any, Tuple
import os, json, logging
from openai import OpenAI
from pydantic import BaseModel

from .models import DesignPrinciple, ClassDesign


# ------------------------------------------------------------------
# Module-level logger
# ------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Configure a basic handler if the application hasn't configured logging yet
    logging.basicConfig(level=os.getenv("LOGLEVEL", "INFO"))


class DesignEvaluator:
    """Evaluate a ``ClassDesign`` against common OO design principles.

    The evaluator currently supports SRP, Encapsulation and Abstraction checks.
    Extend ``self.principles`` with additional private evaluation methods to
    widen the scoring matrix.
    """

    def __init__(self) -> None:
        """Initialize OpenAI client and evaluation settings."""
        # Ensure API key is present for the OpenAI client
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY environment variable not set.")

        # Instantiate the new OpenAI client (SDK ≥1.6)
        self.client = OpenAI()

        # Model configuration – tweak as required
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", 0.2))

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def evaluate_class_design(
        self, class_design: ClassDesign, requirements: str | None = None
    ) -> Dict[str, Any]:
        """Delegate evaluation to OpenAI and return a rich evaluation dictionary.

        The LLM is instructed to respond with JSON exactly matching the schema:

        {
            "overall_score": float (0-10),
            "feedback": [["good|warning|error", "Message"], ...],
            "suggestions": ["..."],
            "design_patterns": ["..."]
        }
        """

        # Build a concise description of the class design
        description = (
            f"Class Name: {class_design.name}\n"
            f"Responsibilities: {', '.join(class_design.responsibilities)}\n"
            f"Attributes: {', '.join(class_design.attributes)}\n"
            f"Methods: {', '.join(class_design.methods)}\n"
            f"Relationships: {', '.join(class_design.relationships)}\n"
        )

        base_system_msg = (
            "You are an expert software design reviewer. "
            "Evaluate the given class design for adherence to SOLID principles, "
            "encapsulation, abstraction, and overall object-oriented quality. "
            "Provide actionable feedback. Respond ONLY with valid JSON matching the schema: "
            "{ 'overall_score': float 0-10, 'feedback': [[level, message], ...], "
            "'suggestions': [...], 'design_patterns': [...] } without code-block markdown."
        )

        # Append the high-level problem requirements (if provided) so the model can
        # judge the class design in the correct context.
        if requirements:
            base_system_msg += f"\n\nProblem Requirements:\n{requirements.strip()}"

        system_msg = base_system_msg

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": description},
        ]

        # Pydantic schema describing the expected structured output
        class _EvalSchema(BaseModel):
            class FeedbackItem(BaseModel):
                level: str
                message: str

            overall_score: float
            feedback: List[FeedbackItem]
            suggestions: List[str]
            design_patterns: List[str]

        try:
            # Use the new responses.parse helper to get structured data
            parsed_resp = self.client.responses.parse(
                model=self.model_name,
                input=messages,
                text_format=_EvalSchema,
            )
            logger.info(f"Parsed response: {parsed_resp}")

            evaluation: Dict[str, Any] = parsed_resp.output_parsed.dict()
            # Detect placeholder feedback (e.g., repeated literal 'message') and treat as invalid
            placeholder_detected = all(
                isinstance(item, dict) and item.get("message", "").strip().lower() == "message"
                for item in evaluation.get("feedback", [])
            )
            if placeholder_detected or not evaluation.get("feedback"):
                raise ValueError("LLM returned placeholder feedback")
        except Exception as exc:
            # Fallback: return minimal structure with error notification
            evaluation = {
                "overall_score": 0,
                "feedback": [("error", f"❌ Failed to parse evaluation: {exc}")],
                "suggestions": [],
                "design_patterns": [],
            }

        # If we still have placeholder feedback or overall_score == 0, use internal heuristic evaluator
        if evaluation.get("overall_score", 0) == 0 or all(
            (isinstance(item, (list, tuple)) and item[1].strip().lower() == "message")
            or (isinstance(item, dict) and item.get("message", "").strip().lower() == "message")
            for item in evaluation.get("feedback", [])
        ):
            evaluation = self._internal_evaluate(class_design)

        return evaluation

    # ------------------------------------------------------------------
    # Individual principle checks (private)
    # ------------------------------------------------------------------
    def _evaluate_srp(self, class_design: ClassDesign) -> tuple[int, List[tuple]]:  # noqa: D401
        """Single-Responsibility Principle evaluation."""
        score = 0
        feedback: List[tuple] = []

        # Check if responsibilities are focused
        if len(class_design.responsibilities) == 1:
            score += 10
            feedback.append(("good", "✅ Single clear responsibility defined"))
        elif len(class_design.responsibilities) <= 3:
            score += 7
            feedback.append(("warning", "⚠️ Multiple responsibilities - consider splitting"))
        else:
            score += 3
            feedback.append(("error", "❌ Too many responsibilities - violates SRP"))

        return score, feedback

    def _evaluate_encapsulation(self, class_design: ClassDesign) -> tuple[int, List[tuple]]:
        score = 0
        feedback: List[tuple] = []
        methods_text = " ".join(class_design.methods).lower()
        if "get" in methods_text or "set" in methods_text:
            score += 8
            feedback.append(("good", "✅ Encapsulation with getter/setter methods"))

        private_attrs = [
            attr
            for attr in class_design.attributes
            if attr.startswith("_") or "private" in attr.lower()
        ]
        if private_attrs:
            score += 5
            feedback.append(("good", "✅ Private attributes identified"))
        else:
            score += 2
            feedback.append(("warning", "⚠️ Consider making some attributes private"))

        return score, feedback

    def _evaluate_abstraction(self, class_design: ClassDesign) -> tuple[int, List[tuple]]:
        score = 0
        feedback: List[tuple] = []
        method_quality = 0
        for method in class_design.methods:
            if any(
                verb in method.lower()
                for verb in ["get", "set", "add", "remove", "update", "create", "delete"]
            ):
                method_quality += 1

        if method_quality >= len(class_design.methods) * 0.8:
            score += 8
            feedback.append(("good", "✅ Well-named methods with clear actions"))
        else:
            score += 5
            feedback.append(("warning", "⚠️ Some methods could have clearer names"))

        return score, feedback

    # ------------------------------------------------------------------
    # Auxiliary helpers
    # ------------------------------------------------------------------
    def _internal_evaluate(self, class_design: ClassDesign) -> Dict[str, Any]:
        """Heuristic evaluation used as fallback when LLM response is invalid."""
        srp_score, srp_feedback = self._evaluate_srp(class_design)
        enc_score, enc_feedback = self._evaluate_encapsulation(class_design)
        abs_score, abs_feedback = self._evaluate_abstraction(class_design)

        total_score = srp_score + enc_score + abs_score  # Max 30
        overall = round((total_score / 30) * 10, 1)

        feedback = srp_feedback + enc_feedback + abs_feedback
        suggestions = self._generate_suggestions(class_design)
        patterns = self._identify_patterns(class_design)

        return {
            "overall_score": overall,
            "feedback": feedback,
            "suggestions": suggestions,
            "design_patterns": patterns,
        }

    @staticmethod
    def _generate_suggestions(class_design: ClassDesign) -> List[str]:
        suggestions: List[str] = []

        if len(class_design.attributes) > 10:
            suggestions.append("Consider grouping related attributes into separate classes")
        if len(class_design.methods) > 15:
            suggestions.append("Large number of methods - consider using composition or inheritance")
        if not any("validate" in method.lower() for method in class_design.methods):
            suggestions.append("Consider adding validation methods for data integrity")
        return suggestions

    @staticmethod
    def _identify_patterns(class_design: ClassDesign) -> List[str]:
        patterns: List[str] = []

        if any("factory" in m.lower() or "create" in m.lower() for m in class_design.methods):
            patterns.append("Factory Pattern")
        if any("observer" in r.lower() or "listener" in r.lower() for r in class_design.relationships):
            patterns.append("Observer Pattern")
        if "builder" in class_design.name.lower():
            patterns.append("Builder Pattern")
        return patterns
