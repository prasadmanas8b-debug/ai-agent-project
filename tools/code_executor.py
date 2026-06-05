"""
tools/code_executor.py — Sandboxed Python code execution tool.

Used by the Coder Agent to safely run generated Python code.
Supports: execution, timeout control, output capture, error capture.
"""

import os
import sys
import subprocess
import tempfile
from typing import Optional


def run_python(code: str, timeout: int = 15, env_vars: Optional[dict] = None) -> dict:
    """
    Execute Python code in an isolated subprocess.

    Args:
        code:     Raw Python code string to execute.
        timeout:  Max seconds before killing the process (default: 15).
        env_vars: Optional dict of extra environment variables.

    Returns:
        {
            "success":    bool,
            "stdout":     str,
            "stderr":     str,
            "returncode": int,
            "timed_out":  bool,
        }
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    env = os.environ.copy()
    if env_vars:
        env.update(env_vars)

    try:
        proc = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        return {
            "success":    proc.returncode == 0,
            "stdout":     proc.stdout.strip(),
            "stderr":     proc.stderr.strip(),
            "returncode": proc.returncode,
            "timed_out":  False,
        }
    except subprocess.TimeoutExpired:
        return {
            "success":    False,
            "stdout":     "",
            "stderr":     f"Execution timed out after {timeout}s.",
            "returncode": -1,
            "timed_out":  True,
        }
    except Exception as e:
        return {
            "success":    False,
            "stdout":     "",
            "stderr":     str(e),
            "returncode": -1,
            "timed_out":  False,
        }
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def format_exec_result(result: dict) -> str:
    """Format execution result into a readable string."""
    if result["success"]:
        return f"✅ Ran successfully\nOutput:\n{result['stdout'] or '(no output)'}"
    elif result["timed_out"]:
        return f"⏱️ Timed out: {result['stderr']}"
    else:
        return f"❌ Failed (exit {result['returncode']})\nError:\n{result['stderr']}"
