import difflib
import os
from typing import Optional
from rich.console import Console
from rich.syntax import Syntax
from rich.prompt import Confirm


def generate_diff(
    original_path: str,
    suggested_fix: str,
    original_content: Optional[str] = None
) -> str:
    """
    Generate a unified diff between original file and suggested fix.
    
    Args:
        original_path: Path to the original file
        suggested_fix: The suggested fix content from LLM
        original_content: Optional original content (if None, reads from file)
    
    Returns:
        Unified diff string
    """
    if original_content is None:
        with open(original_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
    
    original_lines = original_content.splitlines(keepends=True)
    fixed_lines = suggested_fix.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        original_lines,
        fixed_lines,
        fromfile=original_path,
        tofile=f"{original_path} (fixed)",
        lineterm=''
    )
    
    return '\n'.join(diff)


def display_diff(diff: str) -> None:
    """
    Display the diff with color-coding using rich.
    
    Args:
        diff: Unified diff string to display
    """
    console = Console()
    
    # Create syntax object for diff highlighting
    syntax = Syntax(diff, "diff", theme="monokai", line_numbers=True)
    console.print(syntax)


def apply_patch(
    original_path: str,
    suggested_fix: str,
    auto_confirm: bool = False
) -> bool:
    """
    Apply a patch to the original file after user confirmation.
    
    Args:
        original_path: Path to the original file
        suggested_fix: The suggested fix content from LLM
        auto_confirm: If True, skip confirmation prompt
    
    Returns:
        True if patch was applied, False otherwise
    """
    try:
        # Check write permissions
        if os.path.exists(original_path) and not os.access(original_path, os.W_OK):
            console = Console()
            console.print(f"[bold red]Error: Permission denied. File is read-only: {original_path}[/bold red]\n")
            console.print("[bold yellow]Tip: Check file permissions or run with appropriate privileges.[/bold yellow]\n")
            return False
        
        # Read original content
        with open(original_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Generate diff
        diff = generate_diff(original_path, suggested_fix, original_content)
        
        # Display diff
        console = Console()
        console.print("\n[bold cyan]Proposed Changes:[/bold cyan]\n")
        display_diff(diff)
        
        # Prompt for confirmation
        if not auto_confirm:
            console.print("\n[bold yellow]Apply this patch?[/bold yellow]")
            confirmed = Confirm.ask("Confirm", default=False)
        else:
            confirmed = True
        
        if confirmed:
            # Write the fix atomically
            temp_path = f"{original_path}.tmp"
            
            # Write to temp file first
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(suggested_fix)
            
            # Atomic rename
            import os
            os.replace(temp_path, original_path)
            
            console.print("[bold green]✓ Patch applied successfully![/bold green]\n")
            return True
        else:
            console.print("[bold red]✗ Patch cancelled.[/bold red]\n")
            return False
    
    except FileNotFoundError:
        console = Console()
        console.print(f"[bold red]Error: File not found: {original_path}[/bold red]\n")
        return False
    except Exception as e:
        console = Console()
        console.print(f"[bold red]Error applying patch: {e}[/bold red]\n")
        return False


def preview_patch(
    original_path: str,
    suggested_fix: str
) -> str:
    """
    Preview a patch without applying it.
    
    Args:
        original_path: Path to the original file
        suggested_fix: The suggested fix content from LLM
    
    Returns:
        Unified diff string
    """
    return generate_diff(original_path, suggested_fix)
