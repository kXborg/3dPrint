"""
3D Print Failure Detection Monitor

Monitors a webcam feed in real-time using a trained YOLOv8 model to detect
spaghetti, stringing, and warping failures. Can automatically stop the printer
when critical failures are detected.

Usage:
    python print_monitor.py
    python print_monitor.py --config config.yaml
    python print_monitor.py --weights path/to/best.pt --camera 1
"""

import argparse
import os
import time

import cv2
import yaml
from ultralytics import YOLO

from utils.alerts import send_alert
from utils.printer_control import stop_printer


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def monitor_printer(
    model_path: str,
    camera_index=0,
    confidence_threshold: float = 0.5,
    alert_cooldown: int = 60,
    stop_on_spaghetti: bool = True,
    stop_method: str = "printcore",
    printer_port: str = "/dev/ttyUSB0",
    printer_baud: int = 115200,
    relay_ip: str = "192.168.1.100",
    display: bool = True,
    save_frames: bool = True,
    save_dir: str = "alerts",
):
    """
    Main monitoring loop.

    Captures webcam frames, runs YOLOv8 inference, and takes action
    on detected failures.

    Args:
        model_path: Path to trained YOLOv8 weights (.pt file)
        camera_index: Webcam index (0 default, 1 USB) or RTSP URL string
        confidence_threshold: Minimum confidence to trigger alert (0.0 to 1.0)
        alert_cooldown: Seconds between repeated alerts for same failure type
        stop_on_spaghetti: Auto-stop printer on spaghetti detection
        stop_method: "printcore" (USB G-code) or "relay" (WiFi smart plug)
        printer_port: Serial port for printcore method
        printer_baud: Baud rate for printcore method
        relay_ip: Smart plug IP for relay method
        display: Show live detection window
        save_frames: Save alert frames to disk
        save_dir: Directory for saved alert frames
    """
    # ── Load model ───────────────────────────────────────────
    if not os.path.exists(model_path):
        print(f"[ERROR] Model weights not found: {model_path}")
        print("  Train a model first with: python train.py")
        return

    model = YOLO(model_path)
    print(f"[INFO] Model loaded: {model_path}")
    print(f"[INFO] Classes: {model.names}")

    # ── Open camera ──────────────────────────────────────────
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera: {camera_index}")
        print("  Try a different index (0, 1, 2) or check your camera connection")
        return

    print(f"[INFO] Camera opened: {camera_index}")
    print(f"[INFO] Confidence threshold: {confidence_threshold}")
    print(f"[INFO] Alert cooldown: {alert_cooldown}s")
    print(f"[INFO] Auto-stop on spaghetti: {stop_on_spaghetti}")
    print(f"[INFO] Stop method: {stop_method}")
    if display:
        print("[INFO] Press 'q' to quit")
    print()

    # Create save directory
    os.makedirs(save_dir, exist_ok=True)

    # Track alert cooldowns per class
    last_alert_time: dict[str, float] = {}

    frame_count = 0
    start_time = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to capture frame. Camera may have disconnected.")
                break

            frame_count += 1

            # ── Run inference ────────────────────────────────
            results = model(frame, verbose=False, conf=confidence_threshold)

            # ── Process detections ───────────────────────────
            for result in results:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = model.names[cls_id]

                    # Check cooldown
                    now = time.time()
                    if class_name in last_alert_time:
                        elapsed = now - last_alert_time[class_name]
                        if elapsed < alert_cooldown:
                            continue

                    # ── Trigger alert ────────────────────────
                    last_alert_time[class_name] = now
                    send_alert(
                        failure_type=class_name,
                        confidence=confidence,
                        frame=frame,
                        save_dir=save_dir,
                        save_frames=save_frames,
                    )

                    # ── Auto-stop for spaghetti ──────────────
                    if class_name == "spaghetti" and stop_on_spaghetti:
                        print()
                        print("!" * 60)
                        print("  SPAGHETTI DETECTED — STOPPING PRINTER")
                        print("!" * 60)
                        print()

                        stop_printer(
                            method=stop_method,
                            port=printer_port,
                            baud_rate=printer_baud,
                            emergency=True,
                            relay_ip=relay_ip,
                        )

                        # Save final frame and exit
                        cv2.imwrite(
                            os.path.join(save_dir, "spaghetti_stop_frame.jpg"),
                            frame,
                        )
                        cap.release()
                        if display:
                            cv2.destroyAllWindows()
                        return

            # ── Display ──────────────────────────────────────
            if display:
                annotated = results[0].plot()

                # Add FPS counter
                elapsed = time.time() - start_time
                fps = frame_count / elapsed if elapsed > 0 else 0
                cv2.putText(
                    annotated,
                    f"FPS: {fps:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0, 255, 0),
                    2,
                )

                cv2.imshow("Print Failure Monitor", annotated)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("\n[INFO] Quit by user")
                    break

            # ── Throttle to ~1 FPS ───────────────────────────
            # Print failures develop over minutes. 1 FPS is plenty.
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user (Ctrl+C)")

    finally:
        cap.release()
        if display:
            cv2.destroyAllWindows()

        elapsed = time.time() - start_time
        print(f"[INFO] Monitoring stopped after {elapsed:.0f}s ({frame_count} frames)")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor 3D printer for failures using YOLOv8"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )
    parser.add_argument(
        "--weights",
        type=str,
        default=None,
        help="Override model weights path",
    )
    parser.add_argument(
        "--camera",
        default=None,
        help="Override camera index (int) or RTSP URL (string)",
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=None,
        help="Override confidence threshold (0.0 to 1.0)",
    )
    parser.add_argument(
        "--no-display",
        action="store_true",
        help="Run without display window (headless mode)",
    )
    parser.add_argument(
        "--no-stop",
        action="store_true",
        help="Disable auto-stop (alert only mode)",
    )
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Resolve values with CLI overrides
    model_path = args.weights or config["model"]["weights"]

    camera = args.camera or config["camera"]["index"]
    # Try to parse camera as int (for webcam index)
    try:
        camera = int(camera)
    except (ValueError, TypeError):
        pass  # Keep as string (RTSP URL)

    confidence = args.confidence or config["detection"]["confidence_threshold"]
    cooldown = config["detection"]["alert_cooldown"]
    stop_on_spaghetti = config["actions"]["stop_on_spaghetti"] and not args.no_stop
    stop_method = config["actions"]["stop_method"]
    display = config["actions"].get("display", True) and not args.no_display

    printer_port = config["printer"]["port"]
    printer_baud = config["printer"]["baud_rate"]
    relay_ip = config["relay"]["ip"]

    save_frames = config["alerts"]["save_frames"]
    save_dir = config["alerts"]["save_directory"]

    # Run monitor
    monitor_printer(
        model_path=model_path,
        camera_index=camera,
        confidence_threshold=confidence,
        alert_cooldown=cooldown,
        stop_on_spaghetti=stop_on_spaghetti,
        stop_method=stop_method,
        printer_port=printer_port,
        printer_baud=printer_baud,
        relay_ip=relay_ip,
        display=display,
        save_frames=save_frames,
        save_dir=save_dir,
    )


if __name__ == "__main__":
    main()
