from dataclasses import dataclass
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


@dataclass
class ClassDesign:
    """Data-container that represents the design of a single class provided by the user."""

    name: str
    responsibilities: List[str]
    attributes: List[str]
    methods: List[str]
    relationships: List[str]
    code: str = ""
