import time
import sys
from printrun.printcore import printcore

def test_printer_movement(port="COM4", baud=115200):
    print(f"Attempting to connect to printer on {port} at {baud} baud...")
    
    # Initialize printcore
    p = printcore(port, baud)
    p.loud = True
    
    # Callback to catch printer output
    def recv_callback(line):
        print(f"Printer says: {line}")
    p.recvcb = recv_callback
    
    # Wait for the connection to be established and the board to boot
    print("Waiting 5 seconds for printer to initialize...")
    time.sleep(5)
    
    if not p.online:
        print("Failed to connect to the printer. Please check the port and connection.")
        sys.exit(1)
        
    print("Successfully connected to the printer!")
    
    try:
        # Reset printer state in case of any prior BLTouch errors
        print("Releasing BLTouch alarm (M280 P0 S160)...")
        p.send_now("M280 P0 S160")
        time.sleep(2)
        
        print("Sending M999 to reset any error states...")
        p.send_now("M999")
        print("Waiting 5 seconds for reset to take effect...")
        time.sleep(5)
        
        # Home all axes (Default position)
        print("Homing all axes (G28)...")
        p.send_now("G28")
        # Homing takes some time, wait a bit
        time.sleep(15)
        
        # Use Absolute Positioning
        print("Setting absolute positioning (G90)...")
        p.send_now("G90")
        time.sleep(1)
        
        # Move Z axis up to avoid scratching the bed
        print("Moving Z up by 50mm (G1 Z50 F1500)...")
        p.send_now("G1 Z50 F1500")
        time.sleep(5)
        
        # Move X and Y axes
        print("Moving X to 100 and Y to 100 (G1 X100 Y100 F3000)...")
        p.send_now("G1 X100 Y100 F3000")
        time.sleep(5)
        
        # Home again
        print("Returning to default home position (G28)...")
        p.send_now("G28")
        time.sleep(15)
        
    except KeyboardInterrupt:
        print("\nMovement test interrupted by user.")
        
    # Disconnect
    print("Disconnecting...")
    p.disconnect()
    print("Done.")

if __name__ == "__main__":
    test_printer_movement("COM4", 115200)
