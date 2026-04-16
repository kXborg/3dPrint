import os
import random
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

# Class names from data.yaml
CLASS_NAMES = ['spaghetti', 'stringing', 'warping']
CLASS_COLORS = [(255, 50, 50), (50, 200, 50), (80, 120, 255)]  # Red, Green, Blue

def show_samples(split_path, n=5):
    """
    Display random annotated images from a dataset split.

    Args:
        split_path: Path to a split folder (e.g. '3d-print-failure-detection-1/train')
        n: Number of images to display (default 5)
    """
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
                    color = CLASS_COLORS[cls_id]
                    label = CLASS_NAMES[cls_id]

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
        ax.set_title(os.path.basename(split_path), fontsize=11)
        ax.axis("off")

    # Hide unused axes
    for ax in axes[len(samples):]:
        ax.axis("off")

    plt.tight_layout()
    plt.show()
