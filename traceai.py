#!/usr/bin/env python3
"""
TraceAI - Automated Debugging Assistant

An intelligent debugging tool that executes commands, analyzes errors,
and suggests fixes using AI.

Usage:
    traceai.py <command> [--apply] [--timeout SECONDS] [--context LINES]
    traceai.py --traceback FILE [--apply] [--context LINES]
"""

import argparse
import sys
import os
from typing import Optional

from rich.console import Console
from rich.panel import Panel

from engine import TraceAIEngine


def main():
    """Main entry point for TraceAI."""
    console = Console()
    
    parser = argparse.ArgumentParser(
        description="TraceAI: Autonomous terminal debugger that executes commands, analyzes errors using AI, and suggests fixes interactively.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  traceai.py python script.py --apply
  traceai.py npm test --timeout 30
  traceai.py --traceback error.log --context 5
  traceai.py make build --apply --timeout 60

Safety:
  By default, TraceAI runs in dry-run mode and only displays proposed changes.
  Use --apply to automatically apply fixes. Always review diffs before applying.
        """
    )
    
    # Command execution arguments
    parser.add_argument(
        'command',
        nargs='*',
        help='The command to run and debug (e.g., python script.py, npm test, make build)'
    )
    
    parser.add_argument(
        '--traceback',
        '-t',
        type=str,
        help='Path to a file containing a traceback/stack trace to analyze instead of running a command'
    )
    
    parser.add_argument(
        '--apply',
        '-a',
        action='store_true',
        help='Automatically apply the suggested fix. WARNING: This modifies files. Default is dry-run mode.'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=None,
        help='Maximum time in seconds to allow the command to run before terminating (e.g., 30 for 30 seconds)'
    )
    
    parser.add_argument(
        '--context',
        '-c',
        type=int,
        default=10,
        help='Number of code lines to show before and after the error location for context (default: 10)'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='Gemini API key for LLM analysis. Overrides GEMINI_API_KEY environment variable if set.'
    )
    
    parser.add_argument(
        '--version',
        '-v',
        action='version',
        version='TraceAI 1.0.0'
    )
    
    args = parser.parse_args()
    
    # Display banner
    console.print(Panel(
        "[bold cyan]TraceAI[/bold cyan] - [bold white]Automated Debugging Assistant[/bold white]",
        border_style="cyan"
    ))
    console.print()
    
    # Check if we have a command or traceback file
    if not args.command and not args.traceback:
        console.print("[bold red]Error:[/bold red] Either a command or --traceback file must be specified.\n")
        parser.print_help()
        sys.exit(1)
    
    # Initialize the engine
    try:
        engine = TraceAIEngine(api_key=args.api_key)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}\n")
        console.print("[bold yellow]Please set the GEMINI_API_KEY environment variable or use --api-key.[/bold yellow]\n")
        sys.exit(1)
    
    # Warn about --apply flag
    if args.apply:
        console.print("[bold yellow]⚠ WARNING:[/bold yellow] --apply flag is set. TraceAI will modify files automatically.\n")
        console.print("[bold]Safety Note:[/bold] TraceAI performs a dry-run by default. Only with --apply does it modify files.\n")
    else:
        console.print("[bold cyan]ℹ Dry-run mode:[/bold cyan] Use --apply to automatically apply fixes.\n")
    
    # Execute the appropriate mode
    if args.traceback:
        # Analyze traceback file
        engine.analyze_traceback_file(
            traceback_file=args.traceback,
            apply_fix=args.apply,
            context_lines=args.context
        )
    else:
        # Run command and debug
        returncode, stdout, stderr = engine.run_and_debug(
            command=args.command,
            timeout=args.timeout,
            apply_fix=args.apply,
            context_lines=args.context
        )
        
        # Exit with the command's return code
        sys.exit(returncode)


if __name__ == "__main__":
    main()
