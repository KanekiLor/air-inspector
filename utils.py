from __future__ import annotations
import subprocess
import logging
from typing import Tuple, List
import os
import sys

# ---------- Logger ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger("utils")

# ---------- run_cmd ----------

def run_cmd(cmd: List[str], timeout: int | None = 60) -> Tuple[int, str, str]:
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except subprocess.TimeoutExpired as e:
        return -1, "", f"TimeoutExpired: {e}"
    except Exception as e:
        return -1, "", str(e)


# ---------- is_root----------


def is_root() -> bool:
    try:
        return os.geteuid() == 0
    except AttributeError:
        pass


