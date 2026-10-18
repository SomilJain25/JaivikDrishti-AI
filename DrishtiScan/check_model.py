"""
Sanity-check the deployed TFLite model.

Run it on a folder of real leaf photos (any crop) to see whether predictions
vary, or with no arguments to probe with synthetic images. A model whose top-1
class is the same for everything - or whose top confidence is barely above
1/num_classes - has not been trained.

Usage:
    python check_model.py                      # synthetic probe images
    python check_model.py path/to/leaf_photos  # real images (jpg/png)
"""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

try:
    from ai_edge_litert.interpreter import Interpreter
except ImportError:
    import tensorflow as tf

    Interpreter = tf.lite.Interpreter

MODEL_PATH = Path(__file__).parent / "model" / "drishtiscan_model.tflite"
LABELS_PATH = Path(__file__).parent / "model" / "class_labels.json"
SIZE = 224


def load_images(folder):
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    for p in sorted(Path(folder).rglob("*")):
        if p.suffix.lower() in exts:
            img = Image.open(p).convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)
            yield p.name, np.array(img, np.float32) / 255.0


def synthetic_images():
    rng = np.random.default_rng(0)
    for name, rgb in {"green": (128, 200, 100), "brown": (120, 80, 40), "white": (255, 255, 255)}.items():
        yield name, np.full((SIZE, SIZE, 3), rgb, np.float32) / 255.0
    for i in range(5):
        yield f"noise_{i}", rng.random((SIZE, SIZE, 3), dtype=np.float32)


def main():
    labels = json.loads(LABELS_PATH.read_text())["index_to_class"]
    interp = Interpreter(model_path=str(MODEL_PATH))
    interp.allocate_tensors()
    inp, out = interp.get_input_details()[0], interp.get_output_details()[0]

    images = load_images(sys.argv[1]) if len(sys.argv) > 1 else synthetic_images()
    winners, confs = [], []
    for name, arr in images:
        interp.set_tensor(inp["index"], arr[None].astype(np.float32))
        interp.invoke()
        p = np.squeeze(interp.get_tensor(out["index"]).astype(np.float32))
        top = int(np.argmax(p))
        winners.append(labels[str(top)])
        confs.append(float(p[top]))
        print(f"{name:30s} -> {labels[str(top)]} ({p[top] * 100:.1f}%)")

    if not winners:
        sys.exit("No images found.")
    print(f"\n{len(winners)} images, {len(set(winners))} distinct top-1 classes, mean top confidence {np.mean(confs) * 100:.1f}%")
    top_class, count = Counter(winners).most_common(1)[0]
    if len(winners) >= 5 and count / len(winners) > 0.6:
        print(f"WARNING: {count}/{len(winners)} predictions are '{top_class}' - model looks untrained or collapsed.")


if __name__ == "__main__":
    main()
