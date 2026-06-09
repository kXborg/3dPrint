import gradio as gr
import time
from printrun.printcore import printcore

# Global printer instance to maintain connection
# (Connecting causes a reboot on many printers, so we only connect once)
printer = None
sd_files = []

def connect_to_printer(port="COM4", baud=115200):
    global printer
    if printer and printer.online:
        return True
    
    print(f"Connecting to {port}...")
    printer = printcore(port, baud)
    # Wait for board to boot after DTR reset
    time.sleep(5)
    
    if printer.online:
        print("Connected!")
        return True
    else:
        printer = None
        print("Failed to connect.")
        return False

def fetch_models():
    global printer, sd_files
    
    if not connect_to_printer():
        return gr.update(choices=[]), "Error: Could not connect to printer on COM4."
    
    # Clear previous list
    sd_files = []
    
    # Setup temporary callback to capture file list
    def capture_files(line):
        line = str(line).strip()
        # Look for files ending in .GCO or .gcode
        if line.upper().endswith(".GCO") or " " in line and line.split()[0].upper().endswith(".GCO"):
            # Typical Marlin M20 output: "STAND~1.GCO 265672"
            filename = line.split()[0]
            if filename not in sd_files:
                sd_files.append(filename)
                
    old_cb = printer.recvcb
    printer.recvcb = capture_files
    
    try:
        # Initialize SD Card
        printer.send_now("M21")
        time.sleep(1)
        
        # List SD Card files
        printer.send_now("M20")
        time.sleep(3) # Give it time to transmit the list
        
    finally:
        # Restore old callback so we don't leak memory or block
        printer.recvcb = old_cb
        
    if not sd_files:
        return gr.update(choices=[]), "No files found on SD card."
        
    return gr.update(choices=sd_files, value=sd_files[0]), f"Successfully fetched {len(sd_files)} models."

def send_print_command(model_name):
    global printer
    
    if not model_name:
        return "Error: Please select a model first."
        
    if not printer or not printer.online:
        return "Error: Printer disconnected. Please fetch models again to reconnect."
        
    try:
        # Select the file
        printer.send_now(f"M23 {model_name}")
        time.sleep(1)
        
        # Start the print
        printer.send_now("M24")
        return f"Success! Sent print command for {model_name}. The printer should start heating up now."
    except Exception as e:
        return f"Error sending command: {str(e)}"

# Build the Gradio UI
with gr.Blocks(title="3D Print Dashboard", theme=gr.themes.Soft()) as dashboard:
    gr.Markdown(
        """
        # 🖨️ 3D Printer Dashboard
        Fetch models directly from your printer's SD card and start prints remotely via USB.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=1):
            fetch_btn = gr.Button("🔄 Fetch SD Card Models", variant="secondary")
            status_box = gr.Textbox(label="System Status", interactive=False, value="Ready. Click 'Fetch' to connect to printer.")
            
        with gr.Column(scale=2):
            model_radio = gr.Radio(label="Available Models", choices=[], interactive=True)
            print_btn = gr.Button("🚀 Print Selected Model", variant="primary")
            
    # Event wiring
    fetch_btn.click(
        fn=fetch_models, 
        outputs=[model_radio, status_box]
    )
    
    print_btn.click(
        fn=send_print_command, 
        inputs=[model_radio], 
        outputs=[status_box]
    )

if __name__ == "__main__":
    # Launch locally
    print("Starting dashboard on http://127.0.0.1:7860")
    dashboard.launch(server_name="127.0.0.1", server_port=7860)
