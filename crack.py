from utils import run_cmd, logger
from pathlib import Path
import time

def crack_cap(cap_path) -> bool:
    cap_path = Path(cap_path)
    wordlist_path = "/usr/share/wordlists/rockyou.txt"
    cmd = ["aircrack-ng", str(cap_path), "-w", wordlist_path]
    logger.info("Starting aircrack-ng: %s", " ".join(map(str, cmd)))

    rc, stdout, stderr = run_cmd(cmd, timeout=300)

    if rc != 0:
        logger.error("aircrack-ng failed: %s", stderr)
        return False

    for line in stdout.splitlines():
        if "KEY FOUND!" in line:
            logger.info("Password found: %s", line)
            return True

    logger.info("Password not found in the provided wordlist.")
    return False