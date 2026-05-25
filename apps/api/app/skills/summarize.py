from apps.api.app.core.ollama_client import ask_ollama
from apps.api.app.skills.base import BaseSkill, SkillInput, SkillResult


class SummarizeSkill(BaseSkill):
    name = "summarize"
    description = "Summarizes text using the local Ollama model."

    def run(self, skill_input: SkillInput) -> SkillResult:
        prompt = f"""
Summarize the following text clearly and concisely:

{skill_input.text}
"""

        output = ask_ollama(prompt)

        return SkillResult(
            skill_name=self.name,
            output=output,
        )
