import csv
from pathlib import Path
from typing import List, Dict, Optional
 
def parse_scan(csv_path: Path) -> Dict[str, List[Dict]]:
    aps = []
    stations = []
 
    with open(csv_path, newline='', encoding='utf-8', errors='replace') as fh:
        reader = csv.reader(fh)
        rows = list(reader)
 

    ap_header_idx = None
    for i, row in enumerate(rows):
        if row and any(cell.strip().lower() == 'bssid' for cell in row):
            ap_header_idx = i
            break
    if ap_header_idx is None:
        raise ValueError("AP header (BSSID) not found in CSV")
 
    station_header_idx = None
    for j in range(ap_header_idx + 1, len(rows)):
        row = rows[j]
        if not row or all(cell.strip() == "" for cell in row):
            k = j + 1
            while k < len(rows) and (not rows[k] or all(cell.strip() == "" for cell in rows[k])):
                k += 1
            if k < len(rows) and any("station" in (c.strip().lower()) for c in rows[k]):
                station_header_idx = k
            break
 
    ap_columns = [c.strip() for c in rows[ap_header_idx]]
    ap_rows_start = ap_header_idx + 1
    ap_rows_end = station_header_idx - 1 if station_header_idx else len(rows)
 
    for r in rows[ap_rows_start:ap_rows_end]:
        if not r or all(cell.strip() == "" for cell in r):
            continue
        data = {ap_columns[i]: r[i].strip() if i < len(r) else "" for i in range(len(ap_columns))}
        ap = {
            "bssid": data.get("BSSID") or data.get("bssid"),
            "channel": _try_int(data.get("channel") or data.get("CH") or data.get("Channel")),
            "power": _try_int(data.get("Power") or data.get("PWR")),
            "beacons": _try_int(data.get("# beacons") or data.get("Beacons")),
            "essid": data.get("ESSID") or data.get("ESSID") or data.get("ESSID ") or data.get("ESSID"),
            "privacy": data.get("Privacy"),
            "raw": data 
        }
        aps.append(ap)
 
    if station_header_idx:
        station_columns = [c.strip() for c in rows[station_header_idx]]
        for r in rows[station_header_idx + 1:]:
            if not r or all(cell.strip() == "" for cell in r):
                continue
            data = {station_columns[i]: r[i].strip() if i < len(r) else "" for i in range(len(station_columns))}
            st = {
                "station": data.get("Station MAC") or data.get("station"),
                "bssid": data.get("BSSID"),
                "power": _try_int(data.get("Power") or data.get("PWR")),
                "packets": _try_int(data.get("# packets") or data.get("Packets")),
                "probed": data.get("Probed ESSIDs"),
                "raw": data
            }
            stations.append(st)
 
    return {"aps": aps, "stations": stations}
 
 
def _try_int(s):
    if s is None or s == "":
        return None
    try:
        return int(s)
    except Exception:
        try:
            return int(s.strip().strip('*'))
        except Exception:
            return None
 
 
# ---- helper selection funcs ----
 
def choose_ap_by_name(aps: List[Dict], essid: str) -> Optional[Dict]:
    for ap in aps:
        if ap.get("essid") and essid.lower() in ap.get("essid").lower():
            return ap
    return None
 
 
def choose_strongest_ap(aps: List[Dict]) -> Optional[Dict]:

    if not aps:
        return None

    def _power_value(ap: Dict) -> int:
        p = ap.get("power")
        if isinstance(p, (int, float)):
            return int(p)
        try:
            return int(p)
        except Exception:
            return -9999

    return max(aps, key=_power_value)
 
 


if __name__ == "__main__":
    import sys
    from pathlib import Path as _Path
    import pprint

    if len(sys.argv) > 1:
        csv_path = _Path(sys.argv[1])
    else:
        import re

        cwd = _Path('.')
        candidates = list(cwd.glob('test_scan-*.csv'))
        if not candidates:
            raise SystemExit('No test_scan-*.csv files found in current directory; pass a CSV path as argument')

        def _index_of(p: _Path) -> int:
            m = re.search(r'test_scan-(\d+)\.csv$', p.name)
            return int(m.group(1)) if m else -1

        with_index = [( _index_of(p), p) for p in candidates]
        numeric = [t for t in with_index if t[0] >= 0]
        if numeric:
            _, csv_path = max(numeric, key=lambda x: x[0])
        else:
            csv_path = max(candidates, key=lambda p: p.stat().st_mtime)

    result = parse_scan(csv_path)
    pprint.pprint(result)
