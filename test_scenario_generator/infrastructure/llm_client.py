

# test_scenario_generator/infrastructure/llm_client.py
from typing import Dict, Any

from groq import Groq


class LLMClient:
    """Client for interacting with Large Language Models."""
    
    def __init__(self, api_key: str, model: str, temperature: float = 0.2):
        self.client = Groq(api_key=api_key)
        self.model = model
        self.temperature = temperature
    
    def complete(self, prompt: str) -> str:
        """Get a completion from the LLM for the given prompt."""
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "you are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=1024,
                top_p=0.95,
                stop=None,
                stream=False,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"LLM API error: {e}")

