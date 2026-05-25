from abc import ABC, abstractmethod
from pydantic import BaseModel


class SkillInput(BaseModel):
    text: str


class SkillResult(BaseModel):
    skill_name: str
    output: str


class BaseSkill(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, skill_input: SkillInput) -> SkillResult:
        pass
