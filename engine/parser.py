import re
import os
from typing import Optional, Tuple, List


def parse_traceback(traceback_str: str) -> List[Tuple[str, int]]:
    """
    Parse a traceback string to extract file paths and line numbers.
    Supports Python and Node.js stack trace formats.
    
    Args:
        traceback_str: String containing the traceback/stack trace
    
    Returns:
        List of tuples (file_path, line_number) for each stack frame
    """
    frames = []
    
    # Python traceback patterns
    # Pattern 1: File "path/to/file.py", line 42
    python_pattern1 = r'File\s+"([^"]+)",\s+line\s+(\d+)'
    # Pattern 2: path/to/file.py:42
    python_pattern2 = r'([^\s:]+\.py):(\d+)'
    
    # Node.js stack trace patterns
    # Pattern 1: at functionName (path/to/file.js:42:10)
    nodejs_pattern1 = r'at\s+\w+\s+\(([^:]+\.js):(\d+):\d+\)'
    # Pattern 2: at path/to/file.js:42:10
    nodejs_pattern2 = r'at\s+([^:]+\.js):(\d+):\d+'
    
    patterns = [
        python_pattern1,
        python_pattern2,
        nodejs_pattern1,
        nodejs_pattern2
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, traceback_str)
        for match in matches:
            file_path = match.group(1)
            line_number = int(match.group(2))
            # Convert to absolute path to handle execution from different directories
            abs_path = os.path.abspath(file_path)
            frames.append((abs_path, line_number))
    
    return frames


def get_error_context(
    file_path: str,
    line_number: int,
    context_lines: int = 10
) -> Optional[str]:
    """
    Read a file and return the failing line with context.
    
    Args:
        file_path: Path to the source file
        line_number: Line number where the error occurred (1-indexed)
        context_lines: Number of lines to include before and after the error line
    
    Returns:
        String containing the context window, or None if file cannot be read
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Convert to 0-indexed
        error_line_idx = line_number - 1
        
        if error_line_idx < 0 or error_line_idx >= len(lines):
            return None
        
        # Calculate context window
        start_idx = max(0, error_line_idx - context_lines)
        end_idx = min(len(lines), error_line_idx + context_lines + 1)
        
        # Build context string with line numbers
        context_lines_list = []
        for i in range(start_idx, end_idx):
            line_num = i + 1
            prefix = ">>> " if i == error_line_idx else "    "
            context_lines_list.append(f"{prefix}{line_num:4d}: {lines[i].rstrip()}")
        
        return "\n".join(context_lines_list)
    
    except (FileNotFoundError, IOError, UnicodeDecodeError):
        return None


def analyze_traceback(traceback_str: str, context_lines: int = 10) -> List[Tuple[str, int, Optional[str]]]:
    """
    Parse a traceback and extract context for each frame.
    
    Args:
        traceback_str: String containing the traceback/stack trace
        context_lines: Number of lines to include before and after the error line
    
    Returns:
        List of tuples (file_path, line_number, context_string) for each stack frame
    """
    frames = parse_traceback(traceback_str)
    results = []
    
    for file_path, line_number in frames:
        context = get_error_context(file_path, line_number, context_lines)
        results.append((file_path, line_number, context))
    
    return results
