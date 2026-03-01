# 3D Print Failure Detection with YOLOv8

AI-powered 3D print failure detection pipeline using YOLOv8 and OpenCV. Monitors your printer's webcam feed in real-time to detect spaghetti, stringing, and warping — and can automatically stop the printer.

## Project Structure

```
PrintFailureDetection/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── config.yaml               # Configuration (camera, thresholds, printer)
├── train.py                  # Training script (alternative to notebook)
├── train.ipynb               # Training notebook (Colab / Jupyter)
├── print_monitor.py          # Real-time webcam monitoring script
└── utils/
    ├── __init__.py
    ├── alerts.py             # Alert functions (Telegram placeholder)
    └── printer_control.py    # Printer stop functions (printcore / relay)
```

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 2. Train the Model

**Option A: Jupyter Notebook (recommended for first time)**

```bash
jupyter notebook train.ipynb
```

**Option B: Python script**

```bash
# Set your Roboflow API key
export ROBOFLOW_API_KEY="your_api_key_here"

python train.py
```

**Option C: Google Colab**

Upload `train.ipynb` to [Google Colab](https://colab.research.google.com/) for free GPU access.

### 3. Run the Monitor

```bash
python print_monitor.py
```

Press `q` to quit the monitoring window.

## Configuration

Edit `config.yaml` to customize:

```yaml
camera:
  index: 0                    # 0 = default webcam, 1 = USB, or RTSP URL

detection:
  confidence_threshold: 0.5   # Lower = more sensitive
  alert_cooldown: 60          # Seconds between repeated alerts

actions:
  stop_on_spaghetti: true     # Auto-stop on critical failure
  stop_method: "printcore"    # "printcore" (USB) or "relay" (WiFi plug)

printer:
  port: "/dev/ttyUSB0"        # Serial port
  baud_rate: 115200

relay:
  ip: "192.168.1.100"         # Tasmota smart plug IP
```

## Hardware Requirements

- **Training:** NVIDIA GPU with 4GB+ VRAM (or use Google Colab)
- **Inference:** CPU is fine at 1 FPS — prints fail over minutes, not milliseconds
- **Webcam:** Any USB webcam or IP camera (RTSP)

## Dataset

Uses the [3D Print Failure Detection](https://universe.roboflow.com/max-wkf8k/3d-print-failure-detection) dataset by max on Roboflow Universe.

**Classes:** spaghetti, stringing, warping

## License

MIT
