"""Domain data structures for the LLD application (moved from ``LLD.models``)."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class DesignPrinciple(Enum):
    """Enumeration of core design principles used for evaluation."""

    SINGLE_RESPONSIBILITY = "Single Responsibility Principle"
    OPEN_CLOSED = "Open/Closed Principle"
    LISKOV_SUBSTITUTION = "Liskov Substitution Principle"
    INTERFACE_SEGREGATION = "Interface Segregation Principle"
    DEPENDENCY_INVERSION = "Dependency Inversion Principle"
    ENCAPSULATION = "Encapsulation"
    ABSTRACTION = "Abstraction"


class ClassImplementation:
    """Represents the concrete code implementation of a class and its evaluation."""

    code: str = ""
    evaluation: dict = field(default_factory=dict)


@dataclass
class ClassDesign:
    """Data-container that represents the design of a single class provided by the user."""

    name: str
    responsibilities: List[str]
    attributes: List[str]
    methods: List[str]
    relationships: List[str]
    implementation: ClassImplementation = field(default_factory=ClassImplementation)

    # Backward compatibility helpers -------------------------------------
    @property
    def code(self) -> str:  # noqa: D401
        """Proxy to ``implementation.code`` for legacy code."""

        return self.implementation.code

    @code.setter
    def code(self, value: str) -> None:  # noqa: D401
        self.implementation.code = value


__all__ = ["DesignPrinciple", "ClassDesign", "ClassImplementation"]
