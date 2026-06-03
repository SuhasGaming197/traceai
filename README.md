# TraceAI - Automated Debugging Assistant

TraceAI is an intelligent debugging tool that executes commands, analyzes errors using AI, and suggests fixes with interactive patch application. It combines subprocess execution, traceback parsing, LLM-powered analysis, and atomic patching into a unified workflow.

## Features

- **Command Execution**: Run any command with configurable timeout and capture stdout/stderr
- **Traceback Parsing**: Extract file paths and line numbers from Python and Node.js stack traces
- **Context Extraction**: Automatically retrieve code context around error locations
- **AI-Powered Analysis**: Uses Gemini Flash (latest stable version) to generate intelligent fix suggestions.
- **Interactive Patching**: Preview git-style diffs before applying changes
- **Safe by Default**: Dry-run mode ensures developer control over codebase modifications
- **Atomic Operations**: File modifications use atomic writes to prevent corruption

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd CascadeProjects
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Gemini API key:
```bash
export GEMINI_API_KEY="your-api-key-here"
```

## Project Structure

```
CascadeProjects/
├── traceai.py          # Entry point with CLI interface
├── requirements.txt     # Python dependencies
├── README.md          # This file
└── engine/            # Core library
    ├── __init__.py    # Orchestrates the debugging workflow
    ├── executor.py    # Subprocess execution with timeout
    ├── parser.py      # Traceback parsing and context extraction
    ├── llm.py         # Gemini 1.5 Flash client
    └── patcher.py     # Diff generation and patch application
```

## Usage

### Basic Command Execution

Run a command and analyze any errors:
```bash
python traceai.py python script.py
```

### Automatic Fix Application

Apply fixes automatically (use with caution):
```bash
python traceai.py python script.py --apply
```

### Timeout Configuration

Set a timeout for command execution:
```bash
python traceai.py npm test --timeout 30
```

### Context Window Adjustment

Control the number of context lines shown around errors:
```bash
python traceai.py make build --context 5
```

### Analyze Existing Traceback

Analyze a traceback from a file:
```bash
python traceai.py --traceback error.log
```

### API Key Override

Override the environment variable:
```bash
python traceai.py python script.py --api-key "your-api-key"
```

## CLI Options

```
positional arguments:
  command               Command to execute and debug

optional arguments:
  -h, --help            Show help message
  --traceback, -t FILE  Path to a file containing a traceback
  --apply, -a           Automatically apply the suggested fix
  --timeout SECONDS     Timeout for command execution
  --context, -c LINES   Context lines around errors (default: 10)
  --api-key KEY         Gemini API key override
  --version, -v         Show version information
```

## Safety Model

TraceAI implements a **dry-run by default** approach:

1. **Default Mode**: Commands are executed, errors are analyzed, and fixes are suggested. A git-style diff is displayed showing proposed changes. No files are modified.

2. **Apply Mode**: When `--apply` is specified, TraceAI will automatically apply the suggested fix after displaying the diff. This ensures developers remain in total control of their codebase.

3. **Atomic Operations**: All file modifications use atomic writes (temp file + rename) to prevent corruption if the process is interrupted.

## How It Works

1. **Execution**: The command is run using `subprocess.run` with timeout enforcement
2. **Parsing**: If the command fails, the traceback is parsed to extract file paths and line numbers
3. **Context Extraction**: The relevant code is read with a configurable context window
4. **AI Analysis**: Gemini 1.5 Flash analyzes the error and code context to generate a fix
5. **Diff Generation**: A unified diff is generated showing the proposed changes
6. **Interactive Patching**: The diff is displayed with color-coding, and the user can choose to apply it

## Example Workflow

```bash
# Run a failing test
$ python traceai.py python test_broken.py

# TraceAI output:
# ✓ Running command: python test_broken.py
# ✗ Command failed with exit code 1
# ℹ Analyzing error...
# 
# Error location: test_broken.py:42
# Code context:
#    37: def test_calculation():
#    38:     result = calculate(10, 0)
#    39:     assert result == 5
#    40:
# >>> 41: def calculate(a, b):
#    42:     return a / b  # Division by zero error
#    43:
#    44: if __name__ == "__main__":
#    45:     test_calculation()
# 
# ℹ Generating fix suggestion...
# [AI response with fix]
# 
# Proposed fix (dry-run):
# [git-style diff]
# 
# ℹ Run with --apply to apply this fix.

# Apply the fix
$ python traceai.py python test_broken.py --apply
```

## Requirements

- Python 3.8+
- Google Generative AI API key
- Dependencies listed in `requirements.txt`

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
