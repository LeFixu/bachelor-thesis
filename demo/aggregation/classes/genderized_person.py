"""gender module"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from .person import Person


class Gender(Enum):
    """gender enum"""

    FEMALE = 1
    MALE = 2
    NEUTRAL = 3


@dataclass
class GenderizedPerson(Person):
    """GenderizedPerson Class"""

    gender: Optional[Gender]  # Unknown => None
    probability: float
