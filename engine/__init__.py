"""
TraceAI Engine - Orchestrates the debugging workflow.

This module coordinates the execution, parsing, LLM analysis, and patching
components to provide an automated debugging experience.
"""

from typing import Optional, Tuple
from rich.console import Console

from .executor import execute_command
from .parser import parse_traceback, get_error_context, analyze_traceback
from .llm import GeminiClient
from .patcher import generate_diff, display_diff, apply_patch, preview_patch


class TraceAIEngine:
    """Main engine that orchestrates the debugging workflow."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the TraceAI engine.
        
        Args:
            api_key: Gemini API key. If None, reads from GEMINI_API_KEY env var.
        """
        self.console = Console()
        self.llm_client = GeminiClient(api_key)
    
    def run_and_debug(
        self,
        command: list,
        timeout: Optional[int] = None,
        apply_fix: bool = False,
        context_lines: int = 10
    ) -> Tuple[int, str, str]:
        """
        Run a command and automatically debug any errors.
        
        Args:
            command: Command list to execute
            timeout: Optional timeout for command execution
            apply_fix: If True, automatically apply the suggested fix
            context_lines: Number of context lines to show around errors
        
        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        self.console.print(f"[bold cyan]Running command:[/bold cyan] {' '.join(command)}\n")
        
        # Execute the command
        returncode, stdout, stderr = execute_command(command, timeout)
        
        # If successful, return early
        if returncode == 0:
            self.console.print("[bold green]✓ Command executed successfully![/bold green]\n")
            return returncode, stdout, stderr
        
        # Command failed - analyze the error
        self.console.print(f"[bold red]✗ Command failed with exit code {returncode}[/bold red]\n")
        self.console.print("[bold yellow]Analyzing error...[/bold yellow]\n")
        
        # Parse the traceback
        error_frames = parse_traceback(stderr)
        
        if not error_frames:
            self.console.print("[bold yellow]No stack trace found in error output.[/bold yellow]\n")
            self.console.print(f"[bold]Error output:[/bold]\n{stderr}\n")
            return returncode, stdout, stderr
        
        # Get context for the first (most relevant) frame
        file_path, line_number = error_frames[0]
        context = get_error_context(file_path, line_number, context_lines)
        
        if context:
            self.console.print(f"[bold cyan]Error location:[/bold cyan] {file_path}:{line_number}\n")
            self.console.print("[bold]Code context:[/bold]")
            self.console.print(context)
            self.console.print()
        else:
            self.console.print(f"[bold yellow]Could not read file: {file_path}[/bold yellow]\n")
        
        # Generate fix using LLM
        self.console.print("[bold yellow]Generating fix suggestion...[/bold yellow]\n")
        
        error_context = f"Exit code: {returncode}\n\n{stderr}"
        code_context = context or f"File: {file_path}\nLine: {line_number}"
        
        try:
            # Stream the LLM response
            fix_response = ""
            for chunk in self.llm_client.generate_fix(error_context, code_context, stream=True):
                fix_response += chunk
            
            # Extract the code fix from the response
            # This is a simple extraction - in production, you'd want more sophisticated parsing
            suggested_fix = self._extract_code_fix(fix_response)
            
            if suggested_fix:
                # Generate and display diff
                diff = generate_diff(file_path, suggested_fix)
                
                if apply_fix:
                    self.console.print("\n[bold cyan]Applying fix...[/bold cyan]\n")
                    success = apply_patch(file_path, suggested_fix, auto_confirm=True)
                    
                    if success:
                        self.console.print("[bold green]Fix applied successfully![/bold green]\n")
                    else:
                        self.console.print("[bold red]Failed to apply fix.[/bold red]\n")
                else:
                    self.console.print("\n[bold cyan]Proposed fix (dry-run):[/bold cyan]\n")
                    display_diff(diff)
                    self.console.print("\n[bold yellow]Run with --apply to apply this fix.[/bold yellow]\n")
            else:
                self.console.print("[bold yellow]Could not extract code fix from LLM response.[/bold yellow]\n")
        
        except Exception as e:
            self.console.print(f"[bold red]Error generating fix: {e}[/bold red]\n")
        
        return returncode, stdout, stderr
    
    def _extract_code_fix(self, llm_response: str) -> Optional[str]:
        """
        Extract the code fix from the LLM response.
        
        Args:
            llm_response: The full response from the LLM
        
        Returns:
            The extracted code fix, or None if not found
        """
        # Simple heuristic: look for code blocks or the largest section of code
        # In production, you'd want more sophisticated parsing
        
        lines = llm_response.split('\n')
        code_lines = []
        in_code_block = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            
            if in_code_block:
                code_lines.append(line)
        
        if code_lines:
            return '\n'.join(code_lines)
        
        # If no code blocks found, return the entire response
        # (assuming the LLM was instructed to return only code)
        return llm_response
    
    def analyze_traceback_file(
        self,
        traceback_file: str,
        apply_fix: bool = False,
        context_lines: int = 10
    ) -> None:
        """
        Analyze a traceback from a file.
        
        Args:
            traceback_file: Path to file containing traceback
            apply_fix: If True, automatically apply the suggested fix
            context_lines: Number of context lines to show around errors
        """
        with open(traceback_file, 'r') as f:
            traceback_content = f.read()
        
        self.console.print(f"[bold cyan]Analyzing traceback from:[/bold cyan] {traceback_file}\n")
        
        # Analyze the traceback
        frames = analyze_traceback(traceback_content, context_lines)
        
        if not frames:
            self.console.print("[bold yellow]No stack frames found in traceback.[/bold yellow]\n")
            return
        
        # Process the first frame
        file_path, line_number, context = frames[0]
        
        if context:
            self.console.print(f"[bold cyan]Error location:[/bold cyan] {file_path}:{line_number}\n")
            self.console.print("[bold]Code context:[/bold]")
            self.console.print(context)
            self.console.print()
        
        # Generate fix
        self.console.print("[bold yellow]Generating fix suggestion...[/bold yellow]\n")
        
        code_context = context or f"File: {file_path}\nLine: {line_number}"
        
        try:
            fix_response = ""
            for chunk in self.llm_client.generate_fix(traceback_content, code_context, stream=True):
                fix_response += chunk
            
            suggested_fix = self._extract_code_fix(fix_response)
            
            if suggested_fix:
                diff = generate_diff(file_path, suggested_fix)
                
                if apply_fix:
                    self.console.print("\n[bold cyan]Applying fix...[/bold cyan]\n")
                    success = apply_patch(file_path, suggested_fix, auto_confirm=True)
                    
                    if success:
                        self.console.print("[bold green]Fix applied successfully![/bold green]\n")
                    else:
                        self.console.print("[bold red]Failed to apply fix.[/bold red]\n")
                else:
                    self.console.print("\n[bold cyan]Proposed fix (dry-run):[/bold cyan]\n")
                    display_diff(diff)
                    self.console.print("\n[bold yellow]Run with --apply to apply this fix.[/bold yellow]\n")
        
        except Exception as e:
            self.console.print(f"[bold red]Error generating fix: {e}[/bold red]\n")
