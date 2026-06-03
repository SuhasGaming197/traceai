import os
from typing import Iterator
from google import genai
from google.genai import types
from rich.console import Console

class GeminiClient:
    """Client for interacting with the current Google GenAI API."""
    
    def __init__(self, api_key: str | None = None):
        # The client automatically picks up GEMINI_API_KEY from env vars
        self.client = genai.Client(api_key=api_key or os.getenv("GEMINI_API_KEY"))
        self.model_name = "gemini-3.5-flash"
        self.console = Console()
    
    def generate_fix(
        self,
        error_context: str,
        code_context: str,
        stream: bool = True
    ) -> Iterator[str] | str:
        prompt = self._build_prompt(error_context, code_context)
        
        if stream:
            return self._stream_response(prompt)
        else:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            if not response.text or not response.text.strip():
                raise ValueError("LLM returned an empty response.")
            return response.text
    
    def _build_prompt(self, error_context: str, code_context: str) -> str:
        return f"""You are an expert debugging assistant. Analyze the following error and code context to provide a fix.

ERROR CONTEXT:
{error_context}

CODE CONTEXT:
{code_context}

Provide your response in the following format:
1. A brief explanation of the issue
2. The complete fixed code (replace the entire file content with the corrected version)
3. Any additional notes if needed

IMPORTANT: Return ONLY the complete file content for the fix, not just the changed lines."""
    
    def _stream_response(self, prompt: str) -> Iterator[str]:
        response = self.client.models.generate_content_stream(
            model=self.model_name,
            contents=prompt
        )
        
        has_content = False
        for chunk in response:
            if chunk.text:
                has_content = True
                self.console.print(chunk.text, end="")
                yield chunk.text
        
        self.console.print()
        if not has_content:
            raise ValueError("LLM returned an empty response.")
            
    def chat(self, message: str, stream: bool = True) -> Iterator[str] | str:
        if stream:
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=message
            )
            for chunk in response:
                if chunk.text:
                    self.console.print(chunk.text, end="")
                    yield chunk.text
            self.console.print()
        else:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=message
            )
            return response.text
