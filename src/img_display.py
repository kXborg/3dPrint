import os
import random
import colorsys
import yaml
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

# Dataset root directory
DATASET_DIR = os.path.join(os.path.dirname(__file__), "3D-printing-failure-1")

def load_dataset_config(dataset_dir):
    """Load class names and split paths from data.yaml."""
    yaml_path = os.path.join(dataset_dir, "data.yaml")
    with open(yaml_path) as f:
        config = yaml.safe_load(f)

    class_names = config["names"]
    nc = config.get("nc", len(class_names))

    # Generate visually distinct colors for each class
    colors = []
    for i in range(nc):
        hue = i / nc
        r, g, b = colorsys.hls_to_rgb(hue, 0.45, 0.85)
        colors.append((int(r * 255), int(g * 255), int(b * 255)))

    # Resolve split paths relative to dataset_dir
    splits = {}
    for key in ("train", "val", "test"):
        if key in config:
            raw = config[key]  # e.g. "../train/images"
            resolved = os.path.normpath(os.path.join(dataset_dir, raw))
            # Strip trailing /images so split_path points to the split root
            if resolved.endswith(os.sep + "images") or resolved.endswith("/images"):
                resolved = os.path.dirname(resolved)
            splits[key] = resolved

    return class_names, colors, splits


CLASS_NAMES, CLASS_COLORS, SPLITS = load_dataset_config(DATASET_DIR)


def show_samples(split="train", n=5, dataset_dir=None):
    """
    Display random annotated images from a dataset split.

    Args:
        split: Name of the split ('train', 'val', or 'test'), a dataset
               directory path (containing data.yaml), or a direct path
               to a split folder.
        n: Number of images to display (default 5)
        dataset_dir: Optional override for the dataset root directory.
    """
    if dataset_dir:
        names, colors, splits = load_dataset_config(dataset_dir)
    else:
        names, colors, splits = CLASS_NAMES, CLASS_COLORS, SPLITS

    # If split is a dataset directory (contains data.yaml), load it and default to "train"
    candidate = os.path.join(os.path.dirname(__file__), split) if not os.path.isabs(split) else split
    if os.path.isfile(os.path.join(candidate, "data.yaml")):
        names, colors, splits = load_dataset_config(candidate)
        split = "train"

    # Accept either a split name or a direct path
    if split in splits:
        split_path = splits[split]
    else:
        split_path = split  # assume it's a direct path

    img_dir = os.path.join(split_path, "images")
    lbl_dir = os.path.join(split_path, "labels")
    images = [f for f in os.listdir(img_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    samples = random.sample(images, min(n, len(images)))

    cols = 3
    rows = (len(samples) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(18, 6 * rows))
    axes = axes.flatten() if hasattr(axes, 'flatten') else [axes]

    for ax, img_name in zip(axes, samples):
        img = Image.open(os.path.join(img_dir, img_name)).convert("RGB")
        draw = ImageDraw.Draw(img)
        w, h = img.size

        # Load matching label file
        lbl_name = os.path.splitext(img_name)[0] + ".txt"
        lbl_path = os.path.join(lbl_dir, lbl_name)

        if os.path.exists(lbl_path):
            with open(lbl_path) as f:
                for line in f:
                    parts = line.strip().split()
                    cls_id = int(parts[0])
                    vals = list(map(float, parts[1:]))
                    color = colors[cls_id]
                    label = names[cls_id]

                    if len(vals) == 4:
                        # Bounding box format: x_center y_center width height
                        xc, yc, bw, bh = vals
                        x1 = (xc - bw / 2) * w
                        y1 = (yc - bh / 2) * h
                        x2 = (xc + bw / 2) * w
                        y2 = (yc + bh / 2) * h
                        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                        ImageDraw.Draw(overlay).rectangle([x1, y1, x2, y2], fill=(*color, 50), outline=color, width=4)
                        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
                        draw = ImageDraw.Draw(img)
                        tx, ty = x1, y1
                    else:
                        # Segmentation polygon format: x1 y1 x2 y2 ...
                        poly = [(vals[i] * w, vals[i+1] * h) for i in range(0, len(vals), 2)]
                        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                        ImageDraw.Draw(overlay).polygon(poly, fill=(*color, 50), outline=color, width=4)
                        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
                        draw = ImageDraw.Draw(img)
                        tx, ty = poly[0]

                    # Label text
                    draw.rectangle([tx, ty - 14, tx + len(label) * 7 + 4, ty], fill=color)
                    draw.text((tx + 2, ty - 13), label, fill="white")

        ax.imshow(img)
        ax.set_title(split if split in splits else os.path.basename(split_path), fontsize=11)
        ax.axis("off")

    # Hide unused axes
    for ax in axes[len(samples):]:
        ax.axis("off")

    plt.tight_layout()
    plt.show()
