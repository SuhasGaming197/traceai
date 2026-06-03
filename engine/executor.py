import subprocess
from typing import Tuple, Optional


def execute_command(
    command: list,
    timeout: Optional[int] = None
) -> Tuple[int, str, str]:
    """
    Execute a command using subprocess.run with timeout handling.
    
    Args:
        command: List of command arguments (e.g., ['ls', '-la'])
        timeout: Maximum time in seconds to allow the command to run.
                 If None, no timeout is enforced.
    
    Returns:
        Tuple containing:
        - returncode: The exit status of the process (0 for success, non-zero for failure)
        - stdout: The standard output captured from the process
        - stderr: The standard error captured from the process
    
    Raises:
        subprocess.TimeoutExpired: If the process exceeds the timeout
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    
    except subprocess.TimeoutExpired as e:
        # Return timeout information in stderr
        error_msg = f"Command timed out after {timeout} seconds"
        return -1, "", error_msg
