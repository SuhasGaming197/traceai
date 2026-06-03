import os
from typing import Iterator, Optional
import google.generativeai as genai
from rich.console import Console


class GeminiClient:
    """Client for interacting with Gemini 1.5 Flash API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Gemini client.
        
        Args:
            api_key: Google API key. If None, reads from GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable must be set or api_key must be provided"
            )
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.console = Console()
    
    def generate_fix(
        self,
        error_context: str,
        code_context: str,
        stream: bool = True
    ) -> Iterator[str] | str:
        """
        Generate a fix suggestion based on error and code context.
        
        Args:
            error_context: The error message/traceback
            code_context: The relevant code context around the error
            stream: Whether to stream the response
        
        Returns:
            Iterator of response chunks if stream=True, otherwise full response string
        
        Raises:
            ValueError: If the LLM returns an empty or invalid response
        """
        prompt = self._build_prompt(error_context, code_context)
        
        if stream:
            return self._stream_response(prompt)
        else:
            response = self.model.generate_content(prompt)
            if not response.text or not response.text.strip():
                raise ValueError("LLM returned an empty response. Please try again.")
            return response.text
    
    def _build_prompt(self, error_context: str, code_context: str) -> str:
        """Build the prompt for the LLM."""
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
        """Stream the response from the LLM.
        
        Raises:
            ValueError: If the LLM returns an empty or invalid response
        """
        response = self.model.generate_content(prompt, stream=True)
        
        has_content = False
        for chunk in response:
            if chunk.text:
                has_content = True
                self.console.print(chunk.text, end="")
                yield chunk.text
        
        self.console.print()  # New line after streaming completes
        
        if not has_content:
            raise ValueError("LLM returned an empty response. Please try again.")
    
    def chat(self, message: str, stream: bool = True) -> Iterator[str] | str:
        """
        Send a chat message to the LLM.
        
        Args:
            message: The message to send
            stream: Whether to stream the response
        
        Returns:
            Iterator of response chunks if stream=True, otherwise full response string
        """
        if stream:
            response = self.model.generate_content(message, stream=True)
            for chunk in response:
                if chunk.text:
                    self.console.print(chunk.text, end="")
                    yield chunk.text
            self.console.print()
        else:
            response = self.model.generate_content(message)
            return response.text
