"""
Train the DrishtiScan crop-disease classifier.

Why this exists: create_model.py only builds MobileNetV2 with a randomly
initialised classification head and saves it - it never trains it. A model
like that outputs nearly the same (meaningless) distribution for every image,
so every leaf comes back as the same crop. This script actually trains it.

Dataset: PlantVillage, laid out as one folder per class, e.g.
    <data-dir>/Apple___Apple_scab/*.jpg
    <data-dir>/Tomato___Late_blight/*.jpg
(Kaggle: "abdallahalidev/plantvillage-dataset" -> use its "color" folder.)
Folder names must match the names in model/class_labels.json. Only those
classes are used, in exactly that index order, so predict.py needs no change.

Usage:
    python train_model.py --data-dir /path/to/plantvillage/color
    python train_model.py --data-dir ... --epochs-head 5 --epochs-finetune 10

Inputs to the saved model are floats in [0, 1] (what predict.py sends); the
MobileNetV2 [-1, 1] rescaling happens inside the model.
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow import keras

IMAGE_SIZE = 224
MODEL_DIR = Path(__file__).parent / "model"
LABELS_PATH = MODEL_DIR / "class_labels.json"


def load_class_names():
    data = json.loads(LABELS_PATH.read_text())
    index_to_class = data["index_to_class"]
    return [index_to_class[str(i)] for i in range(len(index_to_class))]


def make_datasets(data_dir, class_names, batch_size, seed=42):
    missing = [c for c in class_names if not (Path(data_dir) / c).is_dir()]
    if missing:
        sys.exit(f"Missing class folders in {data_dir}:\n  " + "\n  ".join(missing))

    common = dict(
        directory=data_dir,
        class_names=class_names,  # fixes label index order to match class_labels.json
        label_mode="categorical",
        image_size=(IMAGE_SIZE, IMAGE_SIZE),
        batch_size=batch_size,
        validation_split=0.2,
        seed=seed,
    )
    train = keras.utils.image_dataset_from_directory(subset="training", **common)
    val = keras.utils.image_dataset_from_directory(subset="validation", **common)

    to_unit = lambda x, y: (tf.cast(x, tf.float32) / 255.0, y)  # [0,1], same as predict.py
    train = train.map(to_unit, num_parallel_calls=tf.data.AUTOTUNE).prefetch(tf.data.AUTOTUNE)
    val = val.map(to_unit, num_parallel_calls=tf.data.AUTOTUNE).prefetch(tf.data.AUTOTUNE)
    return train, val


def build_model(num_classes, base_weights="imagenet"):
    augment = keras.Sequential(
        [
            keras.layers.RandomFlip("horizontal_and_vertical"),
            keras.layers.RandomRotation(0.15),
            keras.layers.RandomZoom(0.2),
            keras.layers.RandomContrast(0.2),
            keras.layers.RandomBrightness(0.2, value_range=(0.0, 1.0)),
        ],
        name="augment",
    )
    base = keras.applications.MobileNetV2(
        input_shape=(IMAGE_SIZE, IMAGE_SIZE, 3), include_top=False, weights=base_weights
    )
    base.trainable = False

    inputs = keras.Input(shape=(IMAGE_SIZE, IMAGE_SIZE, 3), dtype="float32")
    x = augment(inputs)  # only active during training
    x = keras.layers.Rescaling(2.0, offset=-1.0, name="to_minus1_1")(x)  # [0,1] -> [-1,1]
    x = base(x, training=False)
    x = keras.layers.GlobalAveragePooling2D()(x)
    x = keras.layers.Dense(256, activation="relu", name="dense_1")(x)
    x = keras.layers.Dropout(0.4, name="dropout_1")(x)
    outputs = keras.layers.Dense(num_classes, activation="softmax", name="predictions")(x)
    return keras.Model(inputs, outputs, name="DrishtiScan_MobileNetV2"), base


def compile_model(model, lr):
    model.compile(
        optimizer=keras.optimizers.Adam(lr),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )


def per_class_report(model, val, class_names):
    y_true, y_pred = [], []
    for x, y in val:
        y_true.extend(np.argmax(y.numpy(), axis=1))
        y_pred.extend(np.argmax(model.predict(x, verbose=0), axis=1))
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    print("\nPer-class validation accuracy:")
    for i, name in enumerate(class_names):
        m = y_true == i
        acc = (y_pred[m] == i).mean() if m.any() else float("nan")
        print(f"  {acc * 100:5.1f}%  {name}  (n={m.sum()})")
    print(f"\nDistinct classes predicted on validation set: {len(set(y_pred.tolist()))} / {len(class_names)}")


def export_tflite(model, out_path):
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    out_path.write_bytes(converter.convert())
    print(f"Saved TFLite model: {out_path} ({out_path.stat().st_size / 1e6:.1f} MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--epochs-head", type=int, default=5)
    ap.add_argument("--epochs-finetune", type=int, default=10)
    ap.add_argument("--unfreeze-last", type=int, default=30, help="base layers to unfreeze when fine-tuning")
    ap.add_argument(
        "--base-weights",
        default="imagenet",
        help='"imagenet" (auto-download) or a path to a local MobileNetV2 no-top .h5 weights file',
    )
    args = ap.parse_args()

    class_names = load_class_names()
    print(f"Training on {len(class_names)} classes")
    train, val = make_datasets(args.data_dir, class_names, args.batch_size)

    model, base = build_model(len(class_names), args.base_weights)

    print("\n== Phase 1: train classifier head (base frozen) ==")
    compile_model(model, 1e-3)
    model.fit(train, validation_data=val, epochs=args.epochs_head)

    print("\n== Phase 2: fine-tune top of the base ==")
    base.trainable = True
    for layer in base.layers[: -args.unfreeze_last]:
        layer.trainable = False
    for layer in base.layers:  # keep BatchNorm statistics fixed
        if isinstance(layer, keras.layers.BatchNormalization):
            layer.trainable = False
    compile_model(model, 1e-5)
    model.fit(
        train,
        validation_data=val,
        epochs=args.epochs_finetune,
        callbacks=[
            keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True, monitor="val_accuracy"),
            keras.callbacks.ReduceLROnPlateau(patience=2, factor=0.5, monitor="val_loss"),
        ],
    )

    loss, acc = model.evaluate(val, verbose=0)
    print(f"\nFinal validation accuracy: {acc * 100:.1f}%")
    per_class_report(model, val, class_names)

    MODEL_DIR.mkdir(exist_ok=True)
    keras_path = MODEL_DIR / "drishtiscan_model.keras"
    model.save(keras_path)
    print(f"Saved Keras model: {keras_path}")
    export_tflite(model, MODEL_DIR / "drishtiscan_model.tflite")
    print("\nNext: python check_model.py   (confirm outputs now vary by input)")


if __name__ == "__main__":
    main()
