from utils import logger
from pathlib import Path
import subprocess
import sys
import re

def crack_cap(cap_path) -> bool:
    cap_path = Path(cap_path)
    wordlist_path = "/usr/share/wordlists/rockyou.txt"
    cmd = ["aircrack-ng", str(cap_path), "-w", wordlist_path]
    logger.info("Starting aircrack-ng: %s", " ".join(map(str, cmd)))

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        key_found = False
        found_password = None

        for line in proc.stdout:
            line = line.rstrip()
            
            progress_match = re.search(r'(\d+)/(\d+)\s+keys\s+tested', line)
            if progress_match:
                tested = int(progress_match.group(1))
                total = int(progress_match.group(2))
                percentage = (tested / total) * 100
                sys.stdout.write(f"\r[Progress] {tested:,}/{total:,} keys tested ({percentage:.2f}%)    ")
                sys.stdout.flush()
            
            if "KEY FOUND!" in line:
                key_found = True
                found_password = line
                print() 
                logger.info("Password found: %s", line)
            
            elif not progress_match and line.strip():
                print(line)

        proc.wait()
        print() 

        if key_found:
            return True

        if proc.returncode != 0:
            logger.error("aircrack-ng failed with return code: %d", proc.returncode)
            return False

        logger.info("Password not found in the provided wordlist.")
        return False

    except Exception as e:
        logger.error("aircrack-ng error: %s", str(e))
        return False