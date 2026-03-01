"""
Printer control functions for 3D print failure detection.

Two methods supported:
1. printcore (USB) — Send G-code commands via Printrun's printcore library
2. relay (WiFi)   — Cut power via ESP8266/Tasmota smart plug HTTP API
"""

import time


def stop_printer_printcore(
    port: str = "/dev/ttyUSB0",
    baud_rate: int = 115200,
    emergency: bool = True,
):
    """
    Stop the printer by sending G-code commands via USB using Printrun's printcore.

    Args:
        port: Serial port (Linux: /dev/ttyUSB0, macOS: /dev/tty.usbserial-*, Windows: COM3)
        baud_rate: Baud rate for serial connection (default: 115200 for Ender 3)
        emergency: If True, send M112 (emergency stop). If False, send M0 (pause).

    Returns:
        True if the stop command was sent successfully, False otherwise.
    """
    try:
        from printrun.printcore import printcore
    except ImportError:
        print("[ERROR] Printrun not installed. Install with: pip install Printrun")
        return False

    try:
        print(f"[PRINTER] Connecting to {port} at {baud_rate} baud...")
        printer = printcore(port, baud_rate)

        # Wait for connection (timeout after 10 seconds)
        timeout = time.time() + 10
        while not printer.online:
            if time.time() > timeout:
                print("[ERROR] Connection timed out. Check port and cable.")
                return False
            time.sleep(0.1)

        print("[PRINTER] Connected successfully")

        if emergency:
            # M112: Emergency stop — kills all heaters and motors immediately
            # Non-resumable, requires printer restart
            printer.send_now("M112")
            print("[PRINTER] Emergency stop sent (M112)")
        else:
            # M0: Unconditional stop — pauses and waits for user input
            # Resumable from printer's LCD
            printer.send_now("M0")
            print("[PRINTER] Pause command sent (M0)")

        # Turn off heaters regardless of stop type
        printer.send_now("M104 S0")  # Hotend off
        printer.send_now("M140 S0")  # Heated bed off
        print("[PRINTER] Heaters turned off")

        # Give commands time to be sent before disconnecting
        time.sleep(1)
        printer.disconnect()
        print("[PRINTER] Disconnected")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to stop printer via printcore: {e}")
        return False


def stop_printer_relay(ip: str = "192.168.1.100", timeout: int = 5):
    """
    Stop the printer by cutting power via a WiFi smart plug (Tasmota firmware).

    Works with any Tasmota-flashed ESP8266 smart plug (Sonoff Basic, S26, etc.)
    Sends an HTTP command to toggle the relay off.

    Args:
        ip: IP address of the Tasmota smart plug on your local network
        timeout: HTTP request timeout in seconds

    Returns:
        True if the power was cut successfully, False otherwise.
    """
    try:
        import requests
    except ImportError:
        print("[ERROR] requests not installed. Install with: pip install requests")
        return False

    try:
        print(f"[RELAY] Sending power off command to {ip}...")
        response = requests.get(
            f"http://{ip}/cm?cmnd=Power%20Off",
            timeout=timeout,
        )

        if response.status_code == 200:
            print(f"[RELAY] Power cut successful via smart plug at {ip}")
            return True
        else:
            print(f"[ERROR] Smart plug returned status {response.status_code}")
            return False

    except Exception as e:
        print(f"[ERROR] Cannot reach smart plug at {ip}: {e}")
        return False


def stop_printer(
    method: str = "printcore",
    port: str = "/dev/ttyUSB0",
    baud_rate: int = 115200,
    emergency: bool = True,
    relay_ip: str = "192.168.1.100",
):
    """
    Stop the printer using the configured method.

    Args:
        method: "printcore" for USB G-code, "relay" for WiFi smart plug
        port: Serial port (for printcore method)
        baud_rate: Baud rate (for printcore method)
        emergency: If True, use emergency stop M112 (for printcore method)
        relay_ip: Smart plug IP address (for relay method)

    Returns:
        True if the stop was successful, False otherwise.
    """
    if method == "printcore":
        return stop_printer_printcore(port, baud_rate, emergency)
    elif method == "relay":
        return stop_printer_relay(relay_ip)
    else:
        print(f"[ERROR] Unknown stop method: {method}. Use 'printcore' or 'relay'.")
        return False
