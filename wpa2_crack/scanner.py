import time
import subprocess
import os
import signal
from pathlib import Path
from utils import logger
 
def scan_once(iface, duration=10, out_prefix=None):
    if out_prefix:
        out_prefix = Path(out_prefix).with_suffix('')
    else:
        out_prefix = Path(f"scan_{int(time.time())}")
 
    csv_path = out_prefix.parent / f"{out_prefix.name}-01.csv"
    cmd = ["airodump-ng", "--write", str(out_prefix), "--output-format", "csv", iface]

    logger.info("Starting scan on interface %s for %d seconds...", iface, duration)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        try:
            proc.wait(timeout=duration)
        except subprocess.TimeoutExpired:
            logger.info("Timer done (%ds). Terminating process group...", duration)
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass

            
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Process did not exit after SIGTERM; killing...")
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                proc.wait()

    except FileNotFoundError as e:
        logger.error("airodump-ng not found: %s", e)
        return None
    except Exception as e:
        logger.error("Failed to start scan process: %s", e)
        return None

    return csv_path if csv_path.exists() else None
 