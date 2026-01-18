"""
Statement models for Discourse Network Analysis.

A statement represents a coded annotation linking an actor to a concept
with a qualifier (agreement/disagreement).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Statement:
    """
    A discourse network statement.

    Represents a coded annotation from a source document, capturing
    who (actor) said what (concept) and their position (qualifier).

    Attributes:
        id: Unique statement identifier
        document_id: Source document ID
        actor: Actor making the statement (organization, person, etc.)
        concept: Concept being referenced
        qualifier: Position on concept (True=agree, False=disagree)
        text: Original text span
        date: Statement date
        coder: Who coded this statement
    """
    id: int
    document_id: int
    actor: str
    concept: str
    qualifier: bool = True
    text: str = ""
    date: Optional[datetime] = None
    coder: str = ""

    def to_data(self) -> "StatementData":
        """Convert to StatementData for network computation."""
        return StatementData(
            id=self.id,
            document_id=self.document_id,
            date_time=self.date or datetime.now(),
            values={
                "actor": self.actor,
                "concept": self.concept,
                "qualifier": str(self.qualifier),
            }
        )


@dataclass
class StatementData:
    """
    Lightweight statement representation for network computation.

    Contains only the data needed for matrix/network calculations.
    """
    id: int
    document_id: int
    date_time: datetime
    values: dict = field(default_factory=dict)
    document_date: Optional[datetime] = None

    def get_value(self, variable: str) -> Optional[str]:
        """Get value for a variable."""
        return self.values.get(variable)
