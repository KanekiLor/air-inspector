from scapy.all import *
from multiprocessing import Process, Manager
import time
import os
import math


def estimate_distance(rssi, frequency_mhz=2437, tx_power=-20, path_loss_exponent=3.0):
    if rssi is None or rssi >= 0:
        return None
    

    rssi_at_1m = tx_power
    
    # Log-Distance Path Loss Model
    # d = 10 ^ ((RSSI_1m - RSSI_measured) / (10 * n))

    try:
        distance = 10 ** ((rssi_at_1m - rssi) / (10 * path_loss_exponent))
        return round(distance, 2)
    except:
        return None


def get_frequency_from_channel(channel):
    """Convert Wi-Fi channel number to frequency in MHz."""
    if channel is None:
        return 2437  
    
    channel = int(channel) if not isinstance(channel, int) else channel
    
    # 2.4 GHz 
    if 1 <= channel <= 14:
        if channel == 14:
            return 2484
        return 2407 + (channel * 5)
    
    # 5 GHz 
    elif 36 <= channel <= 165:
        return 5000 + (channel * 5)
    
    return 2437 


def _signal_worker(iface, target_bssid, results_list):
    def _callback(packet):
        if packet.haslayer(Dot11Beacon):
            bssid = packet[Dot11].addr2
            if bssid == target_bssid:
                try:
                    dbm = packet.dBm_AntSignal
                    results_list.append(dbm)
                except:
                    pass

    sniff(prn=_callback, iface=iface)


def measure_signal(iface, target_bssid, duration=10):
    manager = Manager()
    results_list = manager.list()

    sniff_proc = Process(target=_signal_worker, args=(iface, target_bssid, results_list))
    sniff_proc.start()

    print(f"Scanning for {duration} seconds...")
    for remaining in range(duration, 0, -1):
        print(f"  {remaining}s remaining... ({len(results_list)} readings)", end='\r')
        time.sleep(1)
    print()

    sniff_proc.terminate()
    sniff_proc.join(timeout=2)
    if sniff_proc.is_alive():
        sniff_proc.kill()
        sniff_proc.join()

    readings = list(results_list)
    if not readings:
        return None
    
    avg = sum(readings) / len(readings)
    return avg


def triangulate(iface, target_bssid, target_ssid, channel):
    os.system("clear")
    print("=" * 50)
    print("       Wi-Fi Signal Triangulation")
    print("=" * 50)
    print(f"\nTarget: {target_ssid}")
    print(f"BSSID:  {target_bssid}")
    print(f"Channel: {channel}")
    print("\nThis will take 6 measurements from different positions.")
    print("Follow the instructions and confirm when ready.\n")
    
    frequency = get_frequency_from_channel(channel)

    results = {
        "initial": None,
        "back": None,
        "left": None,
        "right": None
    }

    # Position 1: Initial position
    print("-" * 50)
    print("POSITION 1: Initial Position")
    print("-" * 50)
    input("Stay at your current position. Press Enter to start scanning...")
    
    avg = measure_signal(iface, target_bssid, duration=10)
    if avg is not None:
        results["initial"] = round(avg, 2)
        print(f" Average signal at initial position: {results['initial']} dBm")
    else:
        print(" No signal readings captured at initial position.")
    print()

    # Position 2: 2 steps back
    print("-" * 50)
    print("POSITION 2: Move 2 Steps BACK")
    print("-" * 50)
    input("Move 2 steps BACK from your initial position. Press Enter when ready...")
    
    avg = measure_signal(iface, target_bssid, duration=10)
    if avg is not None:
        results["back"] = round(avg, 2)
        print(f"Average signal 2 steps back: {results['back']} dBm")
    else:
        print(" No signal readings captured at back position.")
    print()

    # Position 3: 2 steps left (from initial)
    print("-" * 50)
    print("POSITION 3: Move 2 Steps LEFT")
    print("-" * 50)
    print("(Return to initial position first, then move 2 steps LEFT)")
    input("Press Enter when ready...")
    
    avg = measure_signal(iface, target_bssid, duration=10)
    if avg is not None:
        results["left"] = round(avg, 2)
        print(f" Average signal 2 steps left: {results['left']} dBm")
    else:
        print(" No signal readings captured at left position.")
    print()

    # Position 4: 2 steps right (from initial)
    print("-" * 50)
    print("POSITION 4: Move 2 Steps RIGHT")
    print("-" * 50)
    print("(Return to initial position first, then move 2 steps RIGHT)")
    input("Press Enter when ready...")
    
    avg = measure_signal(iface, target_bssid, duration=10)
    if avg is not None:
        results["right"] = round(avg, 2)
        print(f" Average signal 2 steps right: {results['right']} dBm")
    else:
        print(" No signal readings captured at right position.")
    print()

     # Position 5: Above you 
    print("-" * 50)
    print("POSITION 5: Hold the DEVICE ABOVE YOU")
    print("-" * 50)
    print("(Return to initial position first, then hold the device above you)")
    input("Press Enter when ready...")
    
    avg = measure_signal(iface, target_bssid, duration=10)
    if avg is not None:
        results["above"] = round(avg, 2)
        print(f" Average signal above you: {results['above']} dBm")
    else:
        print(" No signal readings captured at above position.")
    print()

    # Position 6: Below you
    print("-" * 50)
    print("POSITION 6: Hold the DEVICE BELOW YOU")
    print("-" * 50)
    print("(Return to initial position first, then hold the device below you)")
    input("Press Enter when ready...")
    
    avg = measure_signal(iface, target_bssid, duration=10)
    if avg is not None:
        results["below"] = round(avg, 2)
        print(f" Average signal below you: {results['below']} dBm")
    else:
        print(" No signal readings captured at below position.")
    print()

    # Summary
    print("=" * 50)
    print("       TRIANGULATION RESULTS")
    print("=" * 50)
    print(f"\nTarget: {target_ssid} ({target_bssid})\n")
    print(f"  Initial position:  {results['initial']} dBm")
    print(f"  2 steps BACK:      {results['back']} dBm")
    print(f"  2 steps LEFT:      {results['left']} dBm")
    print(f"  2 steps RIGHT:     {results['right']} dBm")
    print(f"  Above you:         {results['above']} dBm")
    print(f"  Below you:         {results['below']} dBm")
    print()
    
    print("=" * 50)
    print("       DISTANCE ESTIMATION")
    print("=" * 50)
    
    valid_results = {k: v for k, v in results.items() if v is not None}
    
    if valid_results:
        strongest_pos = max(valid_results, key=valid_results.get)
        strongest_rssi = valid_results[strongest_pos]
        avg_rssi = sum(valid_results.values()) / len(valid_results)
        

        dist_outdoor = estimate_distance(strongest_rssi, frequency, tx_power=-20, path_loss_exponent=2.5)
        dist_indoor = estimate_distance(strongest_rssi, frequency, tx_power=-20, path_loss_exponent=3.5)
        dist_avg = estimate_distance(avg_rssi, frequency, tx_power=-20, path_loss_exponent=3.0)
        
        print(f"\n  Strongest signal: {strongest_rssi} dBm (at {strongest_pos} position)")
        print(f"  Average signal:   {avg_rssi:.2f} dBm")
        print(f"  Frequency:        {frequency} MHz (Channel {channel})")
        
        print(f"\n  Estimated distance to AP:")
        if dist_outdoor:
            print(f"    - Outdoor (open area):    ~{dist_outdoor:.1f} meters")
        if dist_indoor:
            print(f"    - Indoor (with walls):    ~{dist_indoor:.1f} meters")
        if dist_avg:
            print(f"    - General estimate:       ~{dist_avg:.1f} meters")
        
        if dist_outdoor and dist_indoor:
            min_dist = min(dist_outdoor, dist_indoor)
            max_dist = max(dist_outdoor, dist_indoor)
            print(f"\n  Estimated range: {min_dist:.1f} - {max_dist:.1f} meters")
        
        print(f"\n  Signal quality:")
        if strongest_rssi >= -50:
            print(f"    Excellent ({strongest_rssi} dBm) - AP is very close!")
        elif strongest_rssi >= -60:
            print(f"    Good ({strongest_rssi} dBm) - AP is nearby")
        elif strongest_rssi >= -70:
            print(f"    Fair ({strongest_rssi} dBm) - AP is at moderate distance")
        elif strongest_rssi >= -80:
            print(f"    Weak ({strongest_rssi} dBm) - AP is far or obstructed")
        else:
            print(f"    Very weak ({strongest_rssi} dBm) - AP is very far or heavily obstructed")
        
        print("\n  Note: Distance estimates are approximate.")
        print("        Walls, obstacles, and interference affect accuracy.")
    print()

    print("=" * 50)
    print("       ESTIMATED LOCATION")
    print("=" * 50)
    
    if len(valid_results) < 2:
        print("\nNot enough valid readings to estimate location.")
    else:
        ns_direction = ""
        if results.get("initial") is not None and results.get("back") is not None:
            if results["back"] > results["initial"]:
                ns_direction = "South" 
            elif results["initial"] > results["back"]:
                ns_direction = "North"  

        ew_direction = ""
        if results.get("left") is not None and results.get("right") is not None:
            if results["left"] > results["right"]:
                ew_direction = "West"  
            elif results["right"] > results["left"]:
                ew_direction = "East"   

        vertical = ""
        if results.get("above") is not None and results.get("below") is not None:
            diff = abs(results["above"] - results["below"])
            if results["above"] > results["below"] and diff > 2:
                vertical = "Above"
            elif results["below"] > results["above"] and diff > 2:
                vertical = "Below"
            else:
                vertical = "Same level"
        elif results.get("above") is not None and results.get("initial") is not None:
            if results["above"] > results["initial"]:
                vertical = "Above"
        elif results.get("below") is not None and results.get("initial") is not None:
            if results["below"] > results["initial"]:
                vertical = "Below"
        
        compass = ""
        if ns_direction and ew_direction:
            compass = f"{ns_direction}-{ew_direction}"
        elif ns_direction:
            compass = ns_direction
        elif ew_direction:
            compass = ew_direction
        else:
            compass = "Center (you may be very close)"
        
        print(f"\n  Horizontal analysis:")
        if results.get("initial") is not None and results.get("back") is not None:
            diff_fb = results["back"] - results["initial"]
            print(f"    Front/Back difference: {diff_fb:+.2f} dBm", end="")
            print(f" → {'Behind you' if diff_fb > 0 else 'In front of you' if diff_fb < 0 else 'Centered'}")
        
        if results.get("left") is not None and results.get("right") is not None:
            diff_lr = results["left"] - results["right"]
            print(f"    Left/Right difference: {diff_lr:+.2f} dBm", end="")
            print(f" → {'To your left' if diff_lr > 0 else 'To your right' if diff_lr < 0 else 'Centered'}")
        
        print(f"\n  Vertical analysis:")
        if results.get("above") is not None and results.get("below") is not None:
            diff_v = results["above"] - results["below"]
            print(f"    Above/Below difference: {diff_v:+.2f} dBm", end="")
            print(f" → {'Above you' if diff_v > 2 else 'Below you' if diff_v < -2 else 'Same level'}")
        
        print("\n" + "-" * 50)
        print("   ESTIMATED AP LOCATION:")
        print("-" * 50)
        print(f"\n  Compass Direction: {compass}")
        if vertical:
            print(f"  Vertical Position: {vertical}")
        
        # Calculate gradient vector for confidence
        # Delta x = Right - Left (positive = AP to the right/East)
        # Delta y = Back - Initial (positive = AP behind/South)  
        # Delta z = Above - Below (positive = AP above)
        
        delta_x = 0  
        delta_y = 0  
        delta_z = 0  
        
        if results.get("left") is not None and results.get("right") is not None:
            delta_x = results["right"] - results["left"]
        
        if results.get("initial") is not None and results.get("back") is not None:
            delta_y = results["back"] - results["initial"]
        
        if results.get("above") is not None and results.get("below") is not None:
            delta_z = results["above"] - results["below"]
        
        # Calculate gradient magnitude: |Delta| = sqrt(Delta_x² + Delta_y² + Delta_z²)
        import math
        gradient_magnitude = math.sqrt(delta_x**2 + delta_y**2 + delta_z**2)
        
        dominant_axis = max(abs(delta_x), abs(delta_y), abs(delta_z))
        
        print(f"\n  Gradient Analysis:")
        print(f"    Delta x (Left→Right): {delta_x:+.2f} dBm")
        print(f"    Delta y (Front→Back): {delta_y:+.2f} dBm")
        print(f"    Delta z (Below→Above): {delta_z:+.2f} dBm")
        print(f"    |Delta| (magnitude): {gradient_magnitude:.2f} dBm")
        print(f"    Dominant axis:   {dominant_axis:.2f} dBm")
        

        
        if gradient_magnitude < 3:
            confidence = "LOW"
            confidence_note = "gradient < 3 dBm (noise level, direction unclear)"
            step_suggestion = "Try larger movements (4-5 steps) for clearer readings"
        elif gradient_magnitude < 6:
            confidence = "MEDIUM"
            confidence_note = "gradient 3-6 dBm (clear directional trend)"
            step_suggestion = "Good readings - continue in suggested direction"
        else:
            confidence = "HIGH"
            confidence_note = "gradient ≥ 6 dBm (strong directional signal)"
            step_suggestion = "Strong signal gradient - AP likely nearby in suggested direction"
        
        strongest = max(valid_results, key=valid_results.get)
        signal_range = max(valid_results.values()) - min(valid_results.values())
        
        print(f"  Confidence: {confidence}")
        print(f"    → {confidence_note}")
        print(f"  Signal range: {signal_range:.2f} dBm (strongest: {valid_results[strongest]} dBm)")
        
        print(f"\n  Result: The AP is likely located to the {compass}", end="")
        if vertical and vertical != "Same level":
            print(f", {vertical.lower()} your current position.")
        else:
            print(", at approximately the same level.")
        
        print("\n  Recommended movement:")
        if ns_direction == "South":
            print("    - Move BACKWARD (away from where you are facing)")
        elif ns_direction == "North":
            print("    - Move FORWARD (the direction you are facing)")
        if ew_direction == "West":
            print("    - Move LEFT")
        elif ew_direction == "East":
            print("    - Move RIGHT")
        if vertical == "Above":
            print("    - Go UP a floor or check ceiling/elevated areas")
        elif vertical == "Below":
            print("    - Go DOWN a floor or check floor-level areas")
        if not ns_direction and not ew_direction and (not vertical or vertical == "Same level"):
            print("    - You may be very close. Check nearby walls and furniture.")
        
        print(f"\n  Step recommendation: {step_suggestion}")

    print()
    
    print("-" * 50)
    restart = input("Do you want to restart the position scanner from a new location? [y/N]: ")
    if restart.strip().lower() in ("y", "yes"):
        print("\nRestarting triangulation... Move to your new starting position.\n")
        return triangulate(iface, target_bssid, target_ssid, channel)
    
    return results


if __name__ == "__main__":
    print("This module is meant to be imported by scan.py")
    print("Run scan.py to use the triangulation feature.")
    
