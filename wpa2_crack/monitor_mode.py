from utils import is_root, run_cmd, logger

def get_interfaces() -> list[str]:
    cmd = ["iwconfig"]
    rc, stdout, stderr = run_cmd(cmd)

    if rc != 0:
        logger.error("Failed to get interfaces: %s", stderr)
        return []

    ifaces: list[str] = []
    for line in stdout.splitlines():
        if line and not line.startswith(' '):
            parts = line.split()
            if parts:
                ifaces.append(parts[0   ])
    return ifaces



def set_monitor_mode(iface: str) -> str | None:
    cmd = ["airmon-ng", "check", "kill"]
    run_cmd(cmd)

    cmd = ["airmon-ng", "start", iface]
    rc, stdout, stderr = run_cmd(cmd)

    if rc != 0:
        logger.error("Failed to enable monitor mode: %s", stderr)
        return None
    else:
        print(f"Monitor mode enabled on interface {iface}")


def set_interfaces():
    if not is_root():
        print("This operation requires root privileges.")
        return None

    print("Running with root privileges.\n")
    interfaces = get_interfaces()
    if not interfaces:
        print("No wireless interfaces found.")
        return None

    for i, iface in enumerate(interfaces, start=1):
        print(f"{i}. {iface}")
    try:
        number = int(input("Enter interface number for the interface you want in monitor mode: "))
        if 1 <= number <= len(interfaces):
            chosen = interfaces[number - 1]
            set_monitor_mode(chosen)
            return chosen
        else:
            print("Invalid selection.")
            return None
    except ValueError:
        print("Invalid input.")
        return None
