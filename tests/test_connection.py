import time
import sys
from printrun.printcore import printcore

def test_printer_connection(port="COM4", baud=115200):
    print(f"Attempting to connect to printer on {port} at {baud} baud...")
    
    # Initialize printcore with loud=True for verbose logging
    p = printcore(port, baud)
    p.loud = True
    
    # Callback to catch printer output
    def recv_callback(line):
        print(f"Printer says: {line}")
    p.recvcb = recv_callback
    
    # Wait for the connection to be established
    time.sleep(3)
    
    if not p.online:
        print("Failed to connect to the printer. Please check the port and connection.")
        sys.exit(1)
        
    print("Successfully connected to the printer!")
    
    # Send M115 to request firmware version and capabilities
    print("Sending M115 (Firmware Info)...")
    p.send_now("M115")
    time.sleep(2)
    
    # Send M105 to request current temperatures
    print("Sending M105 (Get Temperatures)...")
    p.send_now("M105")
    time.sleep(2)
    
    # Disconnect
    print("Disconnecting...")
    p.disconnect()
    print("Done.")

if __name__ == "__main__":
    # You can change the port here if it's different
    test_printer_connection("COM4", 115200)
