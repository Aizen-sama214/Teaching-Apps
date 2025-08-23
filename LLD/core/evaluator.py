"""Evaluator logic migrated from ``LLD.evaluator`` to the core layer."""

# NOTE: copied verbatim from original evaluator.py with only updated imports.

from typing import Dict, List, Any, Tuple
import os, json, logging
from openai import OpenAI
from pydantic import BaseModel, RootModel

from .models import DesignPrinciple, ClassDesign


# ------------------------------------------------------------------
# Module-level logger
# ------------------------------------------------------------------
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=os.getenv("LOGLEVEL", "INFO"))


class DesignEvaluator:  # noqa: WPS230 (large class acceptable)
    """Evaluate a ``ClassDesign`` against common OO design principles."""

    def __init__(self) -> None:  # noqa: D401
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY environment variable not set.")

        self.client = OpenAI()
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.temperature = float(os.getenv("OPENAI_TEMPERATURE", 0.2))

    # ------------------------------------------------------------------
    # Batch evaluation helper (ported from original implementation)
    # ------------------------------------------------------------------

    def evaluate_class_designs(
        self,
        class_designs: Dict[str, ClassDesign],
        requirements: str | None = None,
    ) -> Dict[str, Any]:
        """Evaluate multiple class designs in one LLM request.

        Falls back to individual evaluation when parsing fails.
        """

        if not class_designs:
            return {}

        # Build aggregated description
        description_parts: list[str] = []
        for cd in class_designs.values():
            part = (
                f"Class Name: {cd.name}\n"
                f"Responsibilities: {', '.join(cd.responsibilities)}\n"
                f"Attributes: {', '.join(cd.attributes)}\n"
                f"Methods: {', '.join(cd.methods)}\n"
                f"Relationships: {', '.join(cd.relationships)}"
            )
            description_parts.append(part)

        batched_description = "\n\n---\n\n".join(description_parts)

        system_msg = (
            "You are an expert software design reviewer. "
            "Evaluate each of the following class designs for adherence to SOLID principles, clarity of responsibilities, coupling/cohesion and overall design quality. "
            "Respond ONLY with valid JSON mapping class names to their evaluation. Each value must include 'overall_score', 'feedback', 'suggestions'. "
            "For the field 'feedback', provide a list of tuples, where the first element is the level of the feedback and the second element is the message. "
            "The field 'suggestions' should be a list of strings, where each string is a suggestion for the class."
            "Do not include any markdown code fences or extra keys in the response. "
        )
        if requirements:
            system_msg += f"\n\nProblem Requirements:\n{requirements.strip()}"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": batched_description},
        ]

        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                temperature=self.temperature,
                messages=messages,
            )
            content = resp.choices[0].message.content.strip()
            evaluations = json.loads(content)

            # Ensure all classes present
            if not all(name in evaluations for name in class_designs):
                raise ValueError("Missing class evaluations in response")
            return evaluations
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Batch design evaluation failed (%s). Returning error stubs.", exc,
            )
            return {
                name: {
                    "overall_score": 0,
                    "feedback": [("error", f"Failed to evaluate due to: {exc}")],
                    "suggestions": [],
                }
                for name in class_designs
            }

    # ------------------------------------------------------------------
    # Implementation batch evaluation
    # ------------------------------------------------------------------

    def evaluate_class_implementations(
        self,
        class_impls: Dict[str, str],
        requirements: str | None = None,
    ) -> Dict[str, Any]:
        """Evaluate multiple class *implementations* (actual code) at once.

        The ``class_impls`` mapping should contain class names as keys and the
        full source code of the class as values.  The method sends a single LLM
        request (batch evaluation). When parsing fails we fall back to a simple
        heuristic that scores based on LOC / placeholder usage.
        """

        if not class_impls:
            return {}

        # ------------------------------------------------------------------
        # Build prompt -------------------------------------------------------
        # ------------------------------------------------------------------
        description_parts: list[str] = []
        for name, code in class_impls.items():
            part = f"Class Name: {name}\nCode:\n```python\n{code}\n```"
            description_parts.append(part)

        batched_description = "\n\n---\n\n".join(description_parts)

        system_msg = (
            "You are an expert software engineer and code reviewer. "
            "Evaluate each of the following class *implementations* for code "
            "quality, adherence to SOLID principles, readability, and also suggest "
            "the best design patterns for the class. Respond ONLY with valid JSON mapping class names "
            "to their evaluation. Each value must include 'overall_score', "
            "'feedback', 'suggestions', 'design_patterns'. Do not include any "
            "markdown code fences in the response. The field 'feedback' should be a list of tuples, where the first element is the level of the feedback and the second element is the message."
            "The field 'suggestions' should be a list of strings, where each string is a suggestion for the class."
            "The field 'design_patterns' should be a list of strings, where each string is a design pattern along with an explanation for the class."
        )
        if requirements:
            system_msg += f"\n\nProblem Requirements:\n{requirements.strip()}"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": batched_description},
        ]

        try:
            resp = self.client.chat.completions.create(
                model=self.model_name,
                temperature=self.temperature,
                messages=messages,
            )
            content = resp.choices[0].message.content.strip()
            evaluations = json.loads(content)

            # Ensure all classes present
            if not all(name in evaluations for name in class_impls):
                raise ValueError("Missing implementation evaluations in response")
            return evaluations
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Batch implementation eval failed (%s). Returning error stubs.",
                exc,
            )
            return {
                name: {
                    "overall_score": 0,
                    "feedback": [("error", f"Failed to evaluate due to: {exc}")],
                    "suggestions": [],
                    "design_patterns": [],
                }
                for name in class_impls
            }


__all__ = ["DesignEvaluator"]
