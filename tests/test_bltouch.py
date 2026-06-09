import time
import sys
from printrun.printcore import printcore

def test_bltouch(port="COM4", baud=115200):
    print(f"Connecting to printer on {port} (5V USB power is sufficient)...")
    
    p = printcore(port, baud)
    p.loud = True
    
    def recv_callback(line):
        print(f"Printer says: {line}")
    p.recvcb = recv_callback
    
    time.sleep(5) # Wait for boot
    
    if not p.online:
        print("Failed to connect.")
        sys.exit(1)
        
    print("Connected! Testing BLTouch...")
    
    try:
        # Reset any existing alarms
        print("Releasing alarm (M280 P0 S160)...")
        p.send_now("M280 P0 S160")
        time.sleep(2)
        
        # Deploy pin
        print("Deploying pin (M280 P0 S10)...")
        p.send_now("M280 P0 S10")
        time.sleep(2)
        
        # Stow pin
        print("Stowing pin (M280 P0 S90)...")
        p.send_now("M280 P0 S90")
        time.sleep(2)
        
        # Run self-test
        print("Running continuous self-test (M280 P0 S120)...")
        p.send_now("M280 P0 S120")
        print("Self-test running for 10 seconds. Watch the pin!")
        time.sleep(10)
        
        # Stop self-test by releasing alarm/stowing
        print("Stopping self-test and stowing pin...")
        p.send_now("M280 P0 S160")
        time.sleep(1)
        p.send_now("M280 P0 S90")
        time.sleep(2)
        
    except KeyboardInterrupt:
        print("\nTest interrupted.")
        
    print("Disconnecting...")
    p.disconnect()
    print("Done.")

if __name__ == "__main__":
    test_bltouch("COM4", 115200)
