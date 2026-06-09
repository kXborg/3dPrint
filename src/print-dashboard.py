import gradio as gr
import time
import cv2
import numpy as np
import serial.tools.list_ports
import os
from ultralytics import YOLO
from printrun.printcore import printcore

# Global state
printer = None
sd_files = []
is_monitoring = False

def get_verified_ports():
    """Scan ports and verify which one has an active 3D printer by attempting a connection."""
    global printer
    ports = serial.tools.list_ports.comports()
    
    usb_ports = []
    other_ports = []
    
    for p in ports:
        desc = str(p.description).lower()
        # 3D printers usually use USB-Serial chips like CH340 or FTDI.
        # We want to avoid defaulting to Bluetooth COM ports.
        if ("usb" in desc or "ch340" in desc or "ftdi" in desc or "uart" in desc) and "bluetooth" not in desc:
            usb_ports.append(p.device)
        else:
            other_ports.append(p.device)
            
    all_ports = usb_ports + other_ports
    best_port = all_ports[0] if all_ports else None
    
    # Try to actively verify the printer on the likely USB ports
    if not printer or not printer.online:
        for port in usb_ports:
            print(f"Auto-verifying printer on {port}...")
            try:
                temp_printer = printcore(port, 115200)
                time.sleep(4) # Wait for DTR reset
                if temp_printer.online:
                    print(f"Successfully verified printer on {port}!")
                    printer = temp_printer
                    best_port = port
                    break
                else:
                    temp_printer.disconnect()
            except Exception as e:
                print(f"Verification failed on {port}: {e}")
    elif printer and printer.online:
        best_port = printer.port
        
    return all_ports, best_port

def get_best_camera():
    """Test camera indices 0-5 and return choices sorted by highest resolution."""
    available_cameras = []
    
    for i in range(6):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            available_cameras.append({"index": str(i), "res": w * h, "label": f"Camera {i} ({w}x{h})"})
            cap.release()
            
    if not available_cameras:
        return [("No Cameras Found", "-1")], "-1"
        
    # Sort by resolution descending
    available_cameras.sort(key=lambda x: x["res"], reverse=True)
    
    choices = [(cam["label"], cam["index"]) for cam in available_cameras]
    best_cam = choices[0][1]
    return choices, best_cam

def connect_to_printer(port, baud=115200):
    """Helper to connect globally to the printer, avoiding port locks."""
    global printer
    
    if not port:
        return False, "Error: No port selected."
        
    # If already connected to the same port
    if printer and printer.online and printer.port == port:
        return True, "Already connected."
        
    # If connected to a different port, disconnect first
    if printer and printer.online:
        printer.disconnect()
        
    print(f"Connecting to {port} at {baud} baud...")
    printer = printcore(port, int(baud))
    # Wait for board to boot after DTR reset
    time.sleep(5) 
    
    if printer.online:
        print("Connected!")
        return True, f"Connected to {port}."
    else:
        printer = None
        print("Failed to connect.")
        return False, f"Failed to connect to {port}."

def fetch_models(port):
    """Fetch files from SD Card via M20."""
    global printer, sd_files
    
    success, msg = connect_to_printer(port)
    if not success:
        return gr.update(choices=[]), f"Error: {msg}"
    
    sd_files = []
    
    def capture_files(line):
        line = str(line).strip()
        if line.upper().endswith(".GCO") or " " in line and line.split()[0].upper().endswith(".GCO"):
            filename = line.split()[0]
            if filename not in sd_files:
                sd_files.append(filename)
                
    old_cb = printer.recvcb
    printer.recvcb = capture_files
    
    try:
        printer.send_now("M21")
        time.sleep(1)
        printer.send_now("M20")
        time.sleep(3)
    finally:
        printer.recvcb = old_cb
        
    if not sd_files:
        return gr.update(choices=[]), "No files found on SD card."
        
    return gr.update(choices=sd_files, value=sd_files[0]), f"Successfully fetched {len(sd_files)} models."

def send_print_command(port, model_name):
    """Start printing a model from SD Card."""
    global printer
    
    if not model_name:
        return "Error: Please select a model first."
        
    success, msg = connect_to_printer(port)
    if not success:
        return f"Error: {msg}"
        
    try:
        printer.send_now(f"M23 {model_name}")
        time.sleep(1)
        printer.send_now("M24")
        return f"Success! Sent print command for {model_name}. Printer heating up."
    except Exception as e:
        return f"Error sending command: {str(e)}"

def run_monitor(port, cam_index, model_path, conf_thresh):
    """Generator function that runs YOLO inference and yields frames."""
    global is_monitoring, printer
    
    is_monitoring = True
    
    if int(cam_index) < 0:
        yield None, "Error: No camera found."
        return
        
    if not os.path.exists(model_path):
        yield None, f"Error: Model weights not found at '{model_path}'. Please check the path."
        return
        
    # Load YOLO Model
    try:
        model = YOLO(model_path)
    except Exception as e:
        yield None, f"Error loading model: {str(e)}"
        return
        
    # Open Camera
    cap = cv2.VideoCapture(int(cam_index))
    if not cap.isOpened():
        yield None, f"Error: Cannot open camera {cam_index}"
        return

    status_msg = "Monitoring active... Model loaded successfully."
    
    try:
        while is_monitoring and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                status_msg = "Error reading from camera. Disconnected?"
                break
                
            # Run inference
            results = model(frame, verbose=False, conf=conf_thresh)
            
            # Draw annotations
            annotated = results[0].plot()
            # Convert BGR to RGB for Gradio UI
            annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            
            warning_triggered = False
            
            # Process classes
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    class_name = model.names[cls_id].lower()
                    
                    if class_name == "spaghetti":
                        status_msg = "🚨 CRITICAL: Spaghetti detected! Sending M112 STOP!"
                        
                        # Use global printer object to send emergency stop
                        if printer and printer.online:
                            printer.send_now("M112")
                            printer.send_now("M104 S0") # Heaters off
                            printer.send_now("M140 S0")
                        else:
                            # Attempt rapid reconnect if it disconnected
                            success, _ = connect_to_printer(port)
                            if success:
                                printer.send_now("M112")
                                printer.send_now("M104 S0")
                                printer.send_now("M140 S0")
                        
                        is_monitoring = False
                        break
                        
                    elif class_name in ["zits", "stringing"]:
                        warning_triggered = True
                        status_msg = f"⚠️ WARNING: {class_name.capitalize()} detected. Printer continuing."
                        
            # If spaghetti halted the loop, draw massive text and break
            if not is_monitoring:
                cv2.putText(annotated_rgb, "PRINTER STOPPED", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 4)
                yield annotated_rgb, status_msg
                break
                
            # If just a warning, draw text
            if warning_triggered:
                cv2.putText(annotated_rgb, "WARNING DETECTED", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 165, 0), 3)
            elif status_msg.startswith("Monitoring active"):
                status_msg = "Monitoring active... Printer looking good."
                
            yield annotated_rgb, status_msg
            
            # Throttle processing to ~1 FPS
            time.sleep(1)
            
    finally:
        cap.release()
        is_monitoring = False
        
def stop_monitor():
    """Cancel the monitoring loop."""
    global is_monitoring
    is_monitoring = False
    return "Monitoring stopped by user."

def get_initial_ports():
    """Refresh the UI dropdown for ports."""
    ports, best_port = get_verified_ports()
    return gr.update(choices=ports, value=best_port)

# ─── BUILD THE UI ───────────────────────────────────────────────

with gr.Blocks(title="3D Print Dashboard") as dashboard:
    gr.Markdown("# 3D Print Dashboard | Vision")
    
    with gr.Row():
        # Left Column: Controls
        with gr.Column(scale=1):
            
            # --- 1. Hardware Settings ---
            gr.Markdown("### Hardware Settings")
            initial_ports, verified_port = get_verified_ports()
            port_dropdown = gr.Dropdown(
                label="Printer Port", 
                choices=initial_ports, 
                value=verified_port,
                interactive=True
            )
            refresh_ports_btn = gr.Button("🔄 Refresh Ports", size="sm")
            refresh_ports_btn.click(fn=get_initial_ports, outputs=[port_dropdown])
            
            # --- 2. Print Control ---
            gr.Markdown("### 📄 Print Management")
            fetch_btn = gr.Button("🔄 Fetch SD Card Models", variant="secondary")
            model_radio = gr.Radio(label="Available Models", choices=[], interactive=True)
            print_btn = gr.Button("🚀 Print Selected Model", variant="primary")
            
            # --- 3. AI Settings ---
            gr.Markdown("### 🤖 AI Monitoring Settings")
            cam_choices, best_cam = get_best_camera()
            cam_dropdown = gr.Dropdown(
                label="Camera Selection",
                choices=cam_choices,
                value=best_cam,
                interactive=True
            )
            model_path_input = gr.Textbox(
                label="YOLO Weights Path", 
                value=r"Models\print_failure_detector_v26_nano_4090\weights\best_yolo26n_4090.pt"
            )
            conf_slider = gr.Slider(
                label="Confidence Threshold", 
                minimum=0.1, maximum=1.0, value=0.5, step=0.05
            )
            
            with gr.Row():
                start_monitor_btn = gr.Button("▶️ Start Monitor", variant="primary")
                stop_monitor_btn = gr.Button("⏹️ Stop Monitor")
            
        # Right Column: Video & Status
        with gr.Column(scale=2):
            status_box = gr.Textbox(label="System Status", interactive=False, value="Ready.")
            
            # The streaming image handles real-time updates from our generator
            video_feed = gr.Image(label="Live AI Monitor Feed", streaming=True)
            
    # ─── EVENT WIRING ─────────────────────────────────────────────
    fetch_btn.click(
        fn=fetch_models, 
        inputs=[port_dropdown],
        outputs=[model_radio, status_box]
    )
    
    print_btn.click(
        fn=send_print_command, 
        inputs=[port_dropdown, model_radio], 
        outputs=[status_box]
    )
    
    # Store monitor event so we can cancel it
    monitor_event = start_monitor_btn.click(
        fn=run_monitor,
        inputs=[port_dropdown, cam_dropdown, model_path_input, conf_slider],
        outputs=[video_feed, status_box]
    )
    
    stop_monitor_btn.click(
        fn=stop_monitor,
        outputs=[status_box],
        cancels=[monitor_event]
    )

if __name__ == "__main__":
    print("Starting dashboard on http://127.0.0.1:7860")
    dashboard.launch(server_name="127.0.0.1", server_port=7860, theme=gr.themes.Soft())
