"""
Train a YOLOv8 model on the 3D Print Failure Detection dataset from Roboflow.

Usage:
    # Set your Roboflow API key first
    export ROBOFLOW_API_KEY="your_api_key_here"

    python train.py

    # Or pass the API key as an argument
    python train.py --api-key "your_api_key_here"

    # Customize training
    python train.py --epochs 100 --batch-size 8 --model yolov8s.pt
"""

import argparse
import os
import sys

from roboflow import Roboflow
from ultralytics import YOLO
import yaml


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def download_dataset(api_key: str, config: dict) -> str:
    """
    Download the dataset from Roboflow in YOLOv8 format.

    Returns the path to the dataset's data.yaml file.
    """
    print("=" * 60)
    print("  Downloading Dataset from Roboflow")
    print("=" * 60)

    rf = Roboflow(api_key=api_key)

    workspace = config["dataset"]["workspace"]
    project_name = config["dataset"]["project"]
    version_num = config["dataset"]["version"]
    fmt = config["dataset"]["format"]

    print(f"  Workspace: {workspace}")
    print(f"  Project:   {project_name}")
    print(f"  Version:   {version_num}")
    print(f"  Format:    {fmt}")
    print()

    project = rf.workspace(workspace).project(project_name)
    version = project.version(version_num)
    dataset = version.download(fmt)

    data_yaml_path = os.path.join(dataset.location, "data.yaml")
    print(f"\n  Dataset downloaded to: {dataset.location}")
    print(f"  data.yaml path: {data_yaml_path}")

    return data_yaml_path


def train_model(data_yaml_path: str, config: dict):
    """Train YOLOv8 model on the downloaded dataset."""
    print()
    print("=" * 60)
    print("  Training YOLOv8 Model")
    print("=" * 60)

    base_model = config["training"].get("base_model", "yolov8n.pt")
    epochs = config["training"].get("epochs", 50)
    imgsz = config["training"].get("image_size", 640)
    batch = config["training"].get("batch_size", 16)
    patience = config["training"].get("patience", 10)
    project_name = config["training"].get("project_name", "print_failure_detector")

    print(f"  Base model: {base_model}")
    print(f"  Epochs:     {epochs}")
    print(f"  Image size: {imgsz}")
    print(f"  Batch size: {batch}")
    print(f"  Patience:   {patience}")
    print()

    # Load pretrained model
    model = YOLO(base_model)

    # Train
    results = model.train(
        data=data_yaml_path,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        name=project_name,
        patience=patience,
        save=True,
        plots=True,
    )

    # Print results summary
    print()
    print("=" * 60)
    print("  Training Complete!")
    print("=" * 60)
    print(f"  Best weights: runs/detect/{project_name}/weights/best.pt")
    print(f"  Results:      runs/detect/{project_name}/results.png")
    print(f"  Confusion:    runs/detect/{project_name}/confusion_matrix.png")
    print()

    return model


def evaluate_model(model, config: dict):
    """Run validation on the trained model."""
    print("=" * 60)
    print("  Evaluating Model")
    print("=" * 60)

    metrics = model.val()

    print(f"\n  mAP@0.5:      {metrics.box.map50:.4f}")
    print(f"  mAP@0.5:0.95: {metrics.box.map:.4f}")
    print()

    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="Train YOLOv8 on 3D Print Failure Detection dataset"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Roboflow API key (or set ROBOFLOW_API_KEY env var)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to config file (default: config.yaml)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=None,
        help="Override number of training epochs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help="Override batch size",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override base model (e.g., yolov8n.pt, yolov8s.pt)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip dataset download (use existing dataset)",
    )
    parser.add_argument(
        "--data-yaml",
        type=str,
        default=None,
        help="Path to data.yaml (required if --skip-download)",
    )
    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # CLI overrides
    if args.epochs:
        config["training"]["epochs"] = args.epochs
    if args.batch_size:
        config["training"]["batch_size"] = args.batch_size
    if args.model:
        config["training"]["base_model"] = args.model

    # Get API key
    api_key = args.api_key or os.environ.get("ROBOFLOW_API_KEY")

    # Download dataset
    if args.skip_download:
        if not args.data_yaml:
            print("[ERROR] --data-yaml is required when using --skip-download")
            sys.exit(1)
        data_yaml_path = args.data_yaml
    else:
        if not api_key:
            print("[ERROR] Roboflow API key required.")
            print("  Set ROBOFLOW_API_KEY env var or use --api-key flag")
            sys.exit(1)
        data_yaml_path = download_dataset(api_key, config)

    # Train
    model = train_model(data_yaml_path, config)

    # Evaluate
    evaluate_model(model, config)

    print("Done! You can now run the monitor:")
    print("  python print_monitor.py")


if __name__ == "__main__":
    main()
