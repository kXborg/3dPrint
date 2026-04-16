import os

d = r"c:\Users\User\Desktop\Me\3dPrint\src\3d-print-failure-detection-1"
counts = {}
examples = {}

for split in ["train", "valid", "test"]:
    lbl_dir = os.path.join(d, split, "labels")
    if not os.path.isdir(lbl_dir):
        continue
    for f in os.listdir(lbl_dir):
        if not f.endswith(".txt"):
            continue
        with open(os.path.join(lbl_dir, f), encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                n = len(line.split()) - 1
                counts[n] = counts.get(n, 0) + 1
                if n not in examples or len(examples[n]) < 2:
                    examples.setdefault(n, []).append(line[:120])

print("Annotation format distribution (value count after class_id):")
print("=" * 60)
for k in sorted(counts.keys()):
    label = ""
    if k == 2:
        label = " (POINT: x, y)"
    elif k == 4:
        label = " (BBOX: xc,yc,w,h -or- LINE: 2pts)"
    elif k >= 6:
        label = f" (POLYGON: {k//2} vertices)"
    print(f"  {k} values: {counts[k]:>4} annotations{label}")
    for ex in examples[k]:
        print(f"    -> {ex}")
print(f"\nTotal annotations: {sum(counts.values())}")
