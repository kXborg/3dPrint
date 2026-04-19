# 🖨️ 3D Print Failure Detection

Real-time 3D print failure detection using YOLO26. Point a webcam at your printer, and the system continuously watches for common FDM printing defects — **spaghetti**, **stringing**, and **zits** — and can automatically pause or kill the print before things get worse.

> Built for the Ender-3 V2 Neo, but works with any FDM printer + webcam setup.

## What It Detects

| Defect | Description | Severity |
|--------|-------------|----------|
| 🍝 **Spaghetti** | Print detaches from bed and extrudes into a tangled mess | 🔴 Critical — auto-stops printer |
| 🧵 **Stringing** | Thin filament wisps between travel moves | 🟡 Cosmetic — logs alert |
| 🔵 **Zits** | Small blobs/bumps on the print surface | 🟢 Minor — logs alert |

## How It Works

1. **Train** a YOLO26 nano model on ~9K annotated images of print failures
2. **Monitor** your printer's webcam feed at ~1 FPS (failures develop over minutes, not milliseconds)
3. **Act** — when spaghetti is detected with high confidence, the system sends `M112` (emergency stop) via USB or cuts power via a WiFi smart plug

The trained model runs at **1ms inference** on a GPU and is lightweight enough for CPU inference at 1 FPS.

---

## Project Structure

```
src/
├── README.md                       # This file
├── requirements.txt                # Python dependencies
├── config.yaml                     # Configuration (camera, thresholds, printer)
│
├── train.ipynb                     # Training notebook — Experiment 1 (4.5K image dataset)
├── train_8K.ipynb                  # Training notebook — Experiment 2 (9K image dataset, local GPU)
├── train_8K_RTX_4090.ipynb         # Training notebook — Experiment 3 (9K image dataset, cloud GPU)
├── train.py                        # CLI training script (alternative to notebooks)
│
├── print_monitor.py                # Real-time webcam monitoring + auto-stop
├── img_display.py                  # Visual label inspection & bounding box viewer
├── analyze_labels.py               # Dataset annotation format analysis tool
│
├── 3d-print-failure-detection-1/   # Dataset v1 — poor labels (abandoned)
├── 3D-printing-failure-1/          # Dataset v2 — clean labels (active)
│
├── runs/detect/                    # Training run outputs (weights, plots, metrics)
│   ├── print_failure_detector/             # Exp 1: YOLOv8n baseline
│   ├── print_failure_detector_medium/      # Exp 1: YOLOv8m attempt
│   ├── print_failure_detector_v26_nano*/   # Exp 2: YOLO26n iterations (local)
│   └── print_failure_detector_v26_nano_4090/  # Exp 3: YOLO26n (cloud) ⭐ best
│
├── yolo26n.pt                      # YOLO26 nano pretrained weights
└── yolo26s.pt                      # YOLO26 small pretrained weights
```

---

## Quick Start

### 1. Install Dependencies

```bash
conda create -n 3dprint python=3.14
conda activate 3dprint

pip install -r requirements.txt
```

### 2. Train the Model

**Option A: Jupyter Notebook** (recommended — shows visualizations inline)

```bash
jupyter notebook train_8K.ipynb
```

**Option B: Python script** (headless / scriptable)

```bash
export ROBOFLOW_API_KEY="your_api_key_here"
python train.py --epochs 100 --batch-size 16
```

**Option C: Cloud GPU** (fastest — recommended for production training)

Upload `train_8K_RTX_4090.ipynb` to [RunPod](https://www.runpod.io/) or [Google Colab](https://colab.research.google.com/) with a GPU runtime. An RTX 4090 completes training in ~2.5 hours for ~$1.60.

### 3. Run the Monitor

```bash
python print_monitor.py
```

With custom options:

```bash
python print_monitor.py --weights runs/detect/print_failure_detector_v26_nano_4090/weights/best.pt \
                        --camera 1 \
                        --confidence 0.6
```

Press `q` to quit the monitoring window. Use `--no-display` for headless/server mode.

---

## Configuration

All settings live in `config.yaml`. CLI flags override any config value.

```yaml
model:
  weights: "runs/detect/print_failure_detector_v26_nano_4090/weights/best.pt"

camera:
  index: 0                    # 0 = default webcam, 1 = USB, or RTSP URL string

detection:
  confidence_threshold: 0.5   # Lower = more sensitive, more false positives
  alert_cooldown: 60          # Seconds between repeated alerts per class

actions:
  stop_on_spaghetti: true     # Auto-stop on critical failure
  stop_method: "printcore"    # "printcore" (USB G-code) or "relay" (WiFi smart plug)

printer:
  port: "/dev/ttyUSB0"        # Linux: /dev/ttyUSB0, Windows: COM3
  baud_rate: 115200

relay:
  ip: "192.168.1.100"         # Tasmota-flashed smart plug IP
```

---

## Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Training GPU** | 6GB VRAM (640px, batch=8) | 24GB VRAM (1024px, batch=32) |
| **Inference** | CPU @ 1 FPS | Any GPU — 1ms/frame |
| **Camera** | USB webcam | IP camera (RTSP) for remote setups |
| **Printer control** | USB serial (printcore) | WiFi smart plug (Tasmota relay) |

The model is tiny (2.5M params, 5.2 GFLOPs fused) — inference runs on anything. Training benefits from GPU, but even an RTX 3060 works locally.

---

## Training Experiments

### Experiment 1 — Initial Training (Local, RTX 3060 12GB)

| | |
|---|---|
| **Notebook** | [`train.ipynb`](train.ipynb) |
| **Models** | YOLO26n, YOLO26s |
| **Dataset** | [3D Print Failure Detection v1](https://universe.roboflow.com/bigvision-iwppy/3d-print-failure-detection-efvsh-cewsr/dataset/1) — ~4,500 images |
| **Classes** | spaghetti, stringing, warping |
| **Image size** | 640px |
| **GPU** | NVIDIA RTX 3060 12GB (local) |

**Issues encountered:**

1. **Broken data paths** — Roboflow exported `data.yaml` with relative paths (`../train/images`) that didn't resolve against the working directory. Fixed by rewriting to absolute paths.
2. **CUDA OOM** — Initial batch size of 32 exceeded 12GB VRAM during validation. Reduced to 8.
3. **Poor label quality** — Visual bounding box inspection revealed serious annotation problems: normal prints labeled as "spaghetti", layer lines labeled as defects, overlapping/redundant boxes on the same object.

**Results:**

| Run | Model | Epochs | mAP50 | Notes |
|-----|-------|--------|-------|-------|
| v8 nano | YOLOv8n | 50 | 0.225 | Plateaued immediately |
| v8 medium | YOLOv8m | 50 | 0.220 | Larger model didn't help |
| v26 nano | YOLO26n | 50 | 0.225 | New architecture, same ceiling |
| v26 small | YOLO26s | 150 | 0.258 | More epochs, marginal gain |

**Conclusion:** mAP50 plateaued at ~0.25 regardless of model size, architecture, or training duration. Root cause: dataset label quality. Dataset abandoned.

---

### Experiment 2 — New Dataset (Local, RTX 3060 12GB)

| | |
|---|---|
| **Notebook** | [`train_8K.ipynb`](train_8K.ipynb) |
| **Model** | YOLO26n |
| **Dataset** | [3D Printing Failure](https://universe.roboflow.com/3d-printing-failure/3d-printing-failure) — ~9,000 images, 43K+ boxes |
| **Classes** | spaghetti (9,794), stringing (2,380), zits (31,336) |
| **Image size** | 640px → 800px |
| **GPU** | NVIDIA RTX 3060 12GB (local) |

Switched to a much better-annotated dataset. mAP immediately jumped 3x.

**Results:**

| Run | imgsz | Batch | Epochs | mAP50 | Spaghetti | Stringing | Zits |
|-----|-------|-------|--------|-------|-----------|-----------|------|
| nano4 | 640 | 8 | 50 | 0.622 | 0.930 | 0.566 | 0.370 |
| nano6 | 800 | 16 | 70+ | 0.697 | — | — | — |

**Key findings:**
- Clean labels made all the difference — same model architecture went from 0.225 → 0.622 mAP50
- Image size 640 → 800 improved detection of small defects (zits)
- Loss was still decreasing at epoch 50; model needed more training time
- Batch size limited by 12GB VRAM; higher resolution required dropping batch size

---

### Experiment 3 — Cloud Training (RunPod, RTX 4090 24GB) ⭐ Best

| | |
|---|---|
| **Notebook** | [`train_8K_RTX_4090.ipynb`](train_8K_RTX_4090.ipynb) |
| **Model** | YOLO26n (2.5M params, 5.8 GFLOPs) |
| **Dataset** | [3D Printing Failure](https://universe.roboflow.com/3d-printing-failure/3d-printing-failure) |
| **Image size** | 1024px |
| **Batch size** | 32 |
| **Epochs** | 100 |
| **GPU** | NVIDIA RTX 4090 24GB ([RunPod](https://www.runpod.io/), $0.59/hr) |
| **Training time** | 2 hrs 45 min (~$1.60 total) |

**Training config:**

```python
model = YOLO("yolo26n.pt")
model.train(
    data="3D-printing-failure-1/data.yaml",
    imgsz=1024, batch=32, epochs=100,
    cos_lr=True, patience=20,
    box=8.5, cls=1.0,               # boosted loss weights
    mosaic=1.0, close_mosaic=15,     # mosaic augmentation
    mixup=0.15, copy_paste=0.15,     # instance-level augmentation
    scale=0.7, degrees=10.0,         # geometric augmentation
    shear=2.0, flipud=0.1,
    erasing=0.3,                     # random erasing
    hsv_h=0.02, hsv_s=0.75, hsv_v=0.5,  # color jitter
)
```

**Final results:**

| Class | Precision | Recall | mAP50 | mAP50-95 |
|-------|-----------|--------|-------|----------|
| **All classes** | **0.812** | **0.678** | **0.749** | **0.416** |
| 🍝 Spaghetti | 0.937 | 0.947 | **0.980** | 0.670 |
| 🧵 Stringing | 0.778 | 0.669 | **0.743** | 0.380 |
| 🔵 Zits | 0.720 | 0.419 | **0.524** | 0.198 |

**Inference speed:** 1.0ms/image (1000 FPS) on RTX 4090 | 0.2ms preprocess, 0.1ms postprocess

**Best model:** `runs/detect/print_failure_detector_v26_nano_4090/weights/best.pt` (5.5MB)

---

### Results Summary

```
mAP50 progression across experiments:

Exp 1 — bad dataset, 640px:   █████░░░░░░░░░░░░░░░░░░░░░░░░░  0.225
Exp 2 — clean data, 640px:    ████████████████████░░░░░░░░░░░  0.622
Exp 2 — clean data, 800px:    █████████████████████░░░░░░░░░░  0.697
Exp 3 — clean data, 1024px:   ██████████████████████░░░░░░░░░  0.749
                              ──────────────────────────────→
                              0.0                         1.0
```

### Key Takeaways

1. **Dataset quality >> model size >> training time.** Switching from a poorly-labeled 4.5K dataset to a well-labeled 9K dataset improved mAP50 from 0.225 → 0.622 — a 3x gain with the same model.
2. **Input resolution is the #1 lever for small objects.** 640 → 1024px improved zits detection (mAP50 0.370 → 0.524) because the model can actually see the tiny dots.
3. **YOLO26n (nano) is plenty.** 2.5M params achieved 0.98 mAP50 on spaghetti — the critical defect. Scaling to YOLO26s/m showed no meaningful improvement and wasted compute.
4. **Always visually inspect your labels.** The first dataset looked fine on paper (4.5K images, 3 classes) but had widespread mislabeling — the only way to catch this was plotting bounding boxes on random samples.
5. **Cloud GPU is cost-effective.** A full 100-epoch training run on RTX 4090 cost ~$1.60 total and completed in under 3 hours vs. 5+ hours locally.

---

## Dataset

| | |
|---|---|
| **Source** | [3D Printing Failure](https://universe.roboflow.com/3d-printing-failure/3d-printing-failure) on Roboflow Universe |
| **Images** | ~9,000 (6,159 train / 1,346 val / ~1,500 test) |
| **Annotations** | 43,500+ bounding boxes |
| **Classes** | 3 — spaghetti, stringing, zits |
| **Format** | YOLOv8 (class x_center y_center width height) |

### Class Distribution

```
spaghetti  ████████████████████          9,794  (22.5%)
stringing  █████                         2,380  ( 5.5%)
     zits  ████████████████████████████ 31,336  (72.0%)
```

---

## Tech Stack

- **[Ultralytics](https://github.com/ultralytics/ultralytics)** — YOLO26 model training & inference
- **[OpenCV](https://opencv.org/)** — Webcam capture & frame display
- **[Roboflow](https://roboflow.com/)** — Dataset hosting & download
- **[PyTorch](https://pytorch.org/)** — CUDA-accelerated training backend
- **[Printrun](https://github.com/kliment/Printrun)** — Serial G-code communication for printer control

## License

MIT
