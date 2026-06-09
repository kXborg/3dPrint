import time
import sys
from printrun.printcore import printcore

def test_list_sd_files(port="COM4", baud=115200):
    print(f"Connecting to printer on {port}...")
    
    p = printcore(port, baud)
    p.loud = True
    
    files = []
    
    # Callback to capture printer output
    def recv_callback(line):
        line_str = str(line)
        print(f"Printer says: {line_str}")
        
    p.recvcb = recv_callback
    
    # Wait for the connection to be established
    time.sleep(3)
    
    if not p.online:
        print("Failed to connect to the printer.")
        sys.exit(1)
        
    print("Connected!")
    
    try:
        # Initialize SD card
        print("Initializing SD Card (M21)...")
        p.send_now("M21")
        time.sleep(2)
        
        # Request file list
        print("Listing files on SD Card (M20)...")
        p.send_now("M20")
        
        # Give it a few seconds to print out all the files
        time.sleep(5)
        
        # Optional: release SD card
        # p.send_now("M22")
        
    except KeyboardInterrupt:
        print("\nTest interrupted.")
        
    # Disconnect
    print("Disconnecting...")
    p.disconnect()
    print("Done.")

if __name__ == "__main__":
    test_list_sd_files("COM4", 115200)
